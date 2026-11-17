// Dawgs Uprising -> Unity: the game's RTS camera. WASD / arrows or screen edges pan, the mouse wheel (or + / -) zooms in
// and out toward the cursor, Q / E turn, right-drag tilts, Home resets the view.
// Middle mouse drag, as in the browser game: hold the wheel button and move the mouse to orbit freely (left / right turns
// round the spot you're looking at, up / down tilts), or with Shift to pan (the ground stays under the cursor, like
// grabbing the map). DawgsPrefs.MidPan swaps the two ("Pan · Shift orbits").
// Same rig as the browser game: a target on the ground, a distance, a pitch, a yaw.
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

[RequireComponent(typeof(Camera))]
public class DawgsRtsCamera : MonoBehaviour
{
    public Vector3 target = Vector3.zero;
    public float distance = 110f;
    [Range(0.3f, 1.54f)] public float pitch = 0.98f;   // radians above the horizon
    public float yaw = 0f;                              // radians
    public float minDistance = 18f, maxDistance = 520f;
    public float panSpeed = 1.1f;                       // x distance per second
    public bool edgePan = false;
    public float edgeMargin = 10f;       // px from a screen edge that counts as "against it"
    public Vector2 boundsMin = new Vector2(-700, -300), boundsMax = new Vector2(700, 300);
    public bool keyTurn = true;     // Q / E turn (off in the playable skirmish: Q is the missile key there)
    public bool resetOnHome = true; // Home: back to the default view
    public bool dragTilt = true;    // right-drag tilts (off in the skirmish: right-click gives orders)
    public float zoomStep = 0.86f;  // distance multiplier per wheel notch
    public bool zoomToCursor = true;
    /// set by a HUD: true when the pointer is over it (the wheel then scrolls the HUD, not the camera)
    public static System.Func<Vector2, bool> PointerBlocked;
    float zoomGoal = -1f;           // where a smooth zoom is heading (-1: not zooming)
    bool zoomAtCursor;              // wheel zooms keep the ground under the cursor; keys zoom on the middle of the view
    public const float PitchMin = 0.3f, PitchMax = 1.54f;

    /// true while the middle button is held for a camera drag (the HUD and orders leave the mouse alone)
    public bool MiddleDragging => midDrag;
    bool midDrag; Vector2 midLast; Vector3 grab; bool grabbing;

    /// the browser's Home key: straight-on view at the default tilt
    /// in the editor the pointer must be over the Game view itself (elsewhere the Input System keeps the last position,
    /// often an edge, and the view would slide away on its own)
    static bool PointerInGame()
    {
#if UNITY_EDITOR
        var w = UnityEditor.EditorWindow.mouseOverWindow;
        return w != null && w.GetType().Name == "GameView";
#else
        return true;
#endif
    }

    public void ResetView() { yaw = 0f; pitch = 0.98f; Apply(); }

    /// one step of a middle-button drag from screen point `from` to `to` (pixels): orbit, or pan with the ground held
    /// under the cursor. Public so it can be driven by tests and by other input.
    public void MiddleDrag(Vector2 from, Vector2 to, bool pan)
    {
        Vector2 d = to - from;
        float px = 900f / Mathf.Max(200f, Screen.height);          // the browser's numbers are per CSS pixel of a ~900 px view
        if (!pan)
        {
            grabbing = false;
            yaw -= d.x * 0.006f * px;
            pitch = Mathf.Clamp(pitch - d.y * 0.004f * px, PitchMin, PitchMax);
            return;
        }
        if (!grabbing) { grabbing = Ground(from, out grab); }
        if (grabbing && Ground(to, out var now))
        {
            Vector3 shift = grab - now; shift.y = 0f;
            float lim = distance * 0.25f;                            // near the horizon a pixel is a long way: keep it sane
            if (shift.magnitude > lim) shift = shift.normalized * lim;
            target += shift; ClampTarget(); Apply();
            grabbing = Ground(to, out grab);
        }
        else
        {   // no ground under the cursor (sky): the browser's screen-space pan
            float k = distance / Mathf.Max(200f, Screen.height) * 1.2f;
            Vector3 fwd = new Vector3(-Mathf.Sin(yaw), 0, Mathf.Cos(yaw)), rgt = new Vector3(Mathf.Cos(yaw), 0, Mathf.Sin(yaw));
            target -= (rgt * d.x + fwd * d.y / 0.85f) * k; ClampTarget();
        }
    }

    void ClampTarget()
    {
        target.x = Mathf.Clamp(target.x, boundsMin.x, boundsMax.x);
        target.z = Mathf.Clamp(target.z, boundsMin.y, boundsMax.y);
    }

    /// zoom by wheel notches (positive = in); the camera glides there
    public void ZoomBy(float notches, bool atCursor = false)
    {
        if (Mathf.Abs(notches) < 1e-4f) return;
        if (zoomGoal < 0f) zoomGoal = distance;
        zoomGoal = Mathf.Clamp(zoomGoal * Mathf.Pow(zoomStep, notches), minDistance, maxDistance);
        zoomAtCursor = atCursor;
    }

    void LateUpdate()
    {
        float dt = Time.unscaledDeltaTime;
        Vector2 move = Vector2.zero; float zoom = 0f, keyZoom = 0f, turn = 0f; Vector2 drag = Vector2.zero; bool mid = false, right = false, fast = false;
        Vector2 cursor = new Vector2(Screen.width * 0.5f, Screen.height * 0.5f); bool haveCursor = false;
#if ENABLE_INPUT_SYSTEM
        var kb = Keyboard.current; var ms = Mouse.current;
        if (kb != null)
        {
            bool ctrl = kb.leftCtrlKey.isPressed || kb.rightCtrlKey.isPressed;      // Ctrl+A / Ctrl+S ... are commands, not camera keys
            if ((kb.wKey.isPressed && !ctrl) || kb.upArrowKey.isPressed) move.y += 1;
            if ((kb.sKey.isPressed && !ctrl) || kb.downArrowKey.isPressed) move.y -= 1;
            if ((kb.dKey.isPressed && !ctrl) || kb.rightArrowKey.isPressed) move.x += 1;
            if ((kb.aKey.isPressed && !ctrl) || kb.leftArrowKey.isPressed) move.x -= 1;
            if (keyTurn && kb.qKey.isPressed) turn -= 1;
            if (keyTurn && kb.eKey.isPressed) turn += 1;
            fast = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
            if (kb.homeKey.wasPressedThisFrame && resetOnHome) ResetView();
            // + / - zoom while held (both rows and the keypad)
            if (kb.equalsKey.isPressed || kb.numpadPlusKey.isPressed) keyZoom += 6f * dt;
            if (kb.minusKey.isPressed || kb.numpadMinusKey.isPressed) keyZoom -= 6f * dt;
        }
        if (ms != null)
        {
            // one wheel notch reads 120 on some setups and 1 on others (the Input System's uniform scroll): count notches either way
            float raw = ms.scroll.ReadValue().y;
            float notches = Mathf.Abs(raw) >= 20f ? raw / 120f : raw;
            cursor = ms.position.ReadValue(); haveCursor = true;
            if (notches != 0f && !(PointerBlocked != null && PointerBlocked(cursor))) zoom += notches;
            // middle drag starts only on the battlefield (not over the HUD), then follows the mouse anywhere until released
            if (ms.middleButton.wasPressedThisFrame && !(PointerBlocked != null && PointerBlocked(cursor))) { midDrag = true; midLast = cursor; grabbing = false; zoomGoal = -1f; }
            if (!ms.middleButton.isPressed) { midDrag = false; grabbing = false; }
            mid = midDrag; right = ms.rightButton.isPressed;
            drag = ms.delta.ReadValue();
            if (edgePan && Application.isFocused && !midDrag && PointerInGame())
            {
                // the pointer resting against a screen edge slides the view that way (only while it is inside the window)
                var p = ms.position.ReadValue(); float em = edgeMargin;
                if (p.x >= 0f && p.y >= 0f && p.x <= Screen.width && p.y <= Screen.height)
                {
                    if (p.x < em) move.x -= 1; if (p.x > Screen.width - em) move.x += 1;
                    if (p.y < em) move.y -= 1; if (p.y > Screen.height - em) move.y += 1;
                }
            }
        }
#else
        move = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        if (Input.GetKey(KeyCode.Q)) turn -= 1;
        if (Input.GetKey(KeyCode.E)) turn += 1;
        fast = Input.GetKey(KeyCode.LeftShift);
        cursor = Input.mousePosition; haveCursor = true;
        if (!(PointerBlocked != null && PointerBlocked(cursor))) zoom = Input.mouseScrollDelta.y;
        if (Input.GetKey(KeyCode.Equals) || Input.GetKey(KeyCode.KeypadPlus)) keyZoom += 6f * dt;
        if (Input.GetKey(KeyCode.Minus) || Input.GetKey(KeyCode.KeypadMinus)) keyZoom -= 6f * dt;
        if (Input.GetMouseButtonDown(2) && !(PointerBlocked != null && PointerBlocked(cursor))) { midDrag = true; midLast = cursor; grabbing = false; zoomGoal = -1f; }
        if (!Input.GetMouseButton(2)) { midDrag = false; grabbing = false; }
        mid = midDrag; right = Input.GetMouseButton(1);
        drag = new Vector2(Input.GetAxis("Mouse X"), Input.GetAxis("Mouse Y")) * 10f;
#endif
        // zoom: each notch moves the goal; the camera glides there, keeping the ground under the cursor where it is
        ZoomBy(zoom, true); ZoomBy(keyZoom, false);
        if (zoomGoal > 0f)
        {
            bool anchor = zoomToCursor && zoomAtCursor && haveCursor && cursor.x >= 0 && cursor.y >= 0 && cursor.x <= Screen.width && cursor.y <= Screen.height;
            Vector3 before = Vector3.zero;
            anchor = anchor && Ground(cursor, out before);
            distance = Mathf.Lerp(distance, zoomGoal, 1f - Mathf.Exp(-14f * dt));
            if (Mathf.Abs(distance - zoomGoal) < 0.02f) { distance = zoomGoal; zoomGoal = -1f; }
            if (anchor) { Apply(); if (Ground(cursor, out var after)) { target += before - after; target.y = 0f; } }
        }
        yaw += turn * 1.6f * dt;
        if (mid)
        {   // orbit, or pan with Shift (swapped by the "Pan · Shift orbits" setting)
            bool pan = DawgsPrefs.MidPan ? !fast : fast;
            if (cursor != midLast) MiddleDrag(midLast, cursor, pan);
            midLast = cursor;
            fast = false;                                   // Shift here picks the drag, not a faster key pan
        }
        if (right && dragTilt) pitch = Mathf.Clamp(pitch - drag.y * 0.004f, PitchMin, PitchMax);

        // pan in the camera's ground frame (forward = away from the camera)
        Vector3 fwd = new Vector3(-Mathf.Sin(yaw), 0, Mathf.Cos(yaw)), rgt = new Vector3(Mathf.Cos(yaw), 0, Mathf.Sin(yaw));
        target += (fwd * move.y + rgt * move.x) * distance * panSpeed * (fast ? 2.5f : 1f) * dt;
        ClampTarget();
        Apply();
    }

    public void Apply()
    {
        float hz = distance * Mathf.Cos(pitch);
        // the game puts the eye at target + (hz sin yaw, d sin pitch, hz cos yaw) in its own axes; Unity's z is the game's -z
        transform.position = target + new Vector3(hz * Mathf.Sin(yaw), distance * Mathf.Sin(pitch), -hz * Mathf.Cos(yaw));
        transform.LookAt(new Vector3(target.x, 0f, target.z));
        if (adaptFog && RenderSettings.fog)
        {   // as in the game: the haze starts further out the higher the camera is
            RenderSettings.fogStartDistance = Mathf.Max(320f, distance * 1.25f);
            RenderSettings.fogEndDistance = Mathf.Max(780f, distance * 2.8f);
        }
    }

    public bool adaptFog = true;

    bool Ground(Vector2 screen, out Vector3 p)
    {
        var cam = GetComponent<Camera>(); p = Vector3.zero;
        if (!cam) return false;
        var ray = cam.ScreenPointToRay(screen);
        if (!new Plane(Vector3.up, Vector3.zero).Raycast(ray, out float t) || t > 5000f) return false;
        p = ray.GetPoint(t); return true;
    }

    void OnValidate() { Apply(); }
}
