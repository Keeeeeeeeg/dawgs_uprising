// Dawgs Uprising -> Unity: shared inputs for Dawgs/Lit (every pass uses the same UnityPerMaterial block, so the
// SRP Batcher keeps working). Detail layers: _DetailMap on walls (and everything, if no top maps are set), _TopMap on
// upward faces near the ground, _RoofMap on upward faces higher than _RoofAbove; the terrain's height map tells which.
#ifndef DAWGS_LIT_INPUT_INCLUDED
#define DAWGS_LIT_INPUT_INCLUDED

#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

TEXTURE2D(_BaseMap);        SAMPLER(sampler_BaseMap);
TEXTURE2D(_DetailMap);      SAMPLER(sampler_DetailMap);
TEXTURE2D(_DetailNormal);   SAMPLER(sampler_DetailNormal);
TEXTURE2D(_EmissionMap);    SAMPLER(sampler_EmissionMap);
// upward faces: worn paving low down, roofing up high (both share the detail map's sampler)
TEXTURE2D(_TopMap); TEXTURE2D(_TopNormal); TEXTURE2D(_RoofMap); TEXTURE2D(_RoofNormal);
TEXTURE2D(_GroundHeight);   SAMPLER(sampler_GroundHeight);

CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST;
    half4  _BaseColor;
    half   _VertexColor;
    half   _Smoothness;
    half   _Metallic;
    half4  _EmissionColor;
    half   _Cutoff;
    half   _DetailStrength;
    float  _DetailScale;
    half4  _DetailMean;
    half   _DetailNormalStrength;
    half   _DetailMacro;
    half   _TopStrength;
    half   _TopNormalStrength;
    float  _TopScale;
    half4  _TopMean;
    float  _RoofScale;
    half4  _RoofMean;
    float  _RoofAbove;
    float4 _GroundRect;      // x0, z0 (Unity), 1 / width, 1 / depth of the terrain
    float4 _GroundRange;     // lowest height, height span
    half   _Grime;
    half   _GlassFromAlpha;
    half   _GlassSmoothness;
CBUFFER_END

struct DawgsAttributes
{
    float4 positionOS : POSITION;
    float3 normalOS   : NORMAL;
    half4  color      : COLOR;
    float2 uv         : TEXCOORD0;
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

half4 DawgsBaseColor(float2 uv, half4 vcol)
{
    half4 c = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv) * _BaseColor;
    if (_VertexColor > 0.5h) c.rgb *= vcol.rgb;
    return c;
}

// how far above the terrain a point is (0 when no ground height map is set)
float DawgsAboveGround(float3 pws)
{
    if (_GroundRange.y <= 0.0) return 100.0;
    float2 uv = (pws.xz - _GroundRect.xy) * _GroundRect.zw;
    float g = SAMPLE_TEXTURE2D_LOD(_GroundHeight, sampler_GroundHeight, uv, 0).r * _GroundRange.y + _GroundRange.x;
    return pws.y - g;
}

// world-space triplanar weights (no UVs needed, so any upgraded texture tiles cleanly over the exported meshes)
float3 DawgsTriWeights(float3 n)
{
    float3 w = pow(abs(n), 4.0);
    return w / max(w.x + w.y + w.z, 1e-4);
}

#endif
