// Dawgs Uprising -> Unity: the game's look (vertex colours x flat colour x optional texture), lit by URP's PBR
// lighting with shadows, plus optional world-space (triplanar) detail: a weathered wall surface (Detail Map) on the
// sides, worn paving and roofing (Top / Roof maps) on upward faces - paving near the ground, roofing higher up, told
// apart with the terrain's height map - grime splashed up the foot of the walls, and shiny glass where the Base Map's
// alpha marks windows. Every detail map multiplies the model's own colours (divided by its mean), so paint is kept.
Shader "Dawgs/Lit"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1,1,1,1)
        _BaseMap ("Base Map", 2D) = "white" {}
        [Toggle] _VertexColor ("Use Vertex Colours", Float) = 1
        _Smoothness ("Smoothness", Range(0,1)) = 0.2
        _Metallic ("Metallic", Range(0,1)) = 0
        [HDR] _EmissionColor ("Emission", Color) = (0,0,0,1)
        _EmissionMap ("Emission Map", 2D) = "white" {}
        _Cutoff ("Alpha Cutoff", Range(0,1)) = 0
        [Header(Upgraded detail (world space))]
        _DetailMap ("Detail Albedo", 2D) = "grey" {}
        _DetailMean ("Detail Mean Colour (the map is divided by this)", Color) = (0.5,0.5,0.5,1)
        _DetailStrength ("Detail Strength", Range(0,1.5)) = 0
        _DetailScale ("Detail Tile Size (m)", Float) = 4
        [Normal] _DetailNormal ("Detail Normal", 2D) = "bump" {}
        _DetailNormalStrength ("Detail Normal Strength", Range(0,2)) = 0
        _DetailMacro ("Large Weathering (Detail alpha at 4x size)", Range(0,1.5)) = 0
        [Header(Upward faces (paving low down, roofing up high))]
        _TopStrength ("Top Strength (0 = use Detail Albedo on top too)", Range(0,1.5)) = 0
        _TopNormalStrength ("Top Normal Strength", Range(0,2)) = 0
        _TopMap ("Paving Albedo", 2D) = "grey" {}
        [Normal] _TopNormal ("Paving Normal", 2D) = "bump" {}
        _TopScale ("Paving Tile Size (m)", Float) = 5
        _TopMean ("Paving Mean Colour", Color) = (0.5,0.5,0.5,1)
        _RoofMap ("Roofing Albedo", 2D) = "grey" {}
        [Normal] _RoofNormal ("Roofing Normal", 2D) = "bump" {}
        _RoofScale ("Roofing Tile Size (m)", Float) = 6
        _RoofMean ("Roofing Mean Colour", Color) = (0.5,0.5,0.5,1)
        _RoofAbove ("Roofs start this high above the ground (m)", Float) = 2.5
        [Header(Weathering)]
        _Grime ("Grime at the foot of walls", Range(0,1)) = 0
        [Toggle] _GlassFromAlpha ("Base Map alpha marks glass", Float) = 0
        _GlassSmoothness ("Glass Smoothness", Range(0,1)) = 0.86
        [NoScaleOffset] _GroundHeight ("Ground Height (set by Dawgs > Upgrade Ground and Buildings)", 2D) = "black" {}
        _GroundRect ("Ground Rect", Vector) = (0,0,0,0)
        _GroundRange ("Ground Range", Vector) = (0,0,0,0)
        [HideInInspector] _SrcBlend ("__src", Float) = 1
        [HideInInspector] _DstBlend ("__dst", Float) = 0
        [HideInInspector] _ZWrite ("__zw", Float) = 1
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            #include "DawgsLitInput.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                half4  color      : COLOR;
                float2 uv         : TEXCOORD2;
                half   fogCoord   : TEXCOORD3;
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(DawgsAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                VertexNormalInputs n = GetVertexNormalInputs(v.normalOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.color = v.color;
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.fogCoord = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i, bool front : SV_IsFrontFace) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                half4 c = DawgsBaseColor(i.uv, i.color);
                if (_Cutoff > 0.001h) clip(c.a - _Cutoff);

                float3 nWS = normalize(i.normalWS);
                nWS = front ? nWS : -nWS;

                half smooth = _Smoothness;
                if (_GlassFromAlpha > 0.5h) { smooth = lerp(_GlassSmoothness, _Smoothness, saturate(c.a)); c.a = 1.0h; }

                float above = 100.0;
                if (_Grime > 0.001h || _TopStrength > 0.001h) above = DawgsAboveGround(i.positionWS);

                if (_DetailStrength > 0.001h || _DetailNormalStrength > 0.001h || _TopStrength > 0.001h)
                {
                    float3 w = DawgsTriWeights(nWS);
                    float3 p = i.positionWS / max(_DetailScale, 0.01);
                    bool top = _TopStrength > 0.001h && w.y > 0.001;
                    half3 d = half3(0, 0, 0);
                    if (_DetailStrength > 0.001h)
                    {
                        half3 dx = SAMPLE_TEXTURE2D(_DetailMap, sampler_DetailMap, p.zy).rgb;
                        half3 dz = SAMPLE_TEXTURE2D(_DetailMap, sampler_DetailMap, p.xy).rgb;
                        half3 side = (dx * w.x + dz * w.z) / max(_DetailMean.rgb, 0.02h);
                        if (_DetailMacro > 0.001h)
                        {   // rain runs, damp and sun-bleached patches a few storeys tall, so a wall reads as weathered from afar
                            half mx = SAMPLE_TEXTURE2D(_DetailMap, sampler_DetailMap, p.zy * 0.25).a;
                            half mz = SAMPLE_TEXTURE2D(_DetailMap, sampler_DetailMap, p.xy * 0.25).a;
                            half macro = (mx * w.x + mz * w.z) / max((half)(w.x + w.z), 0.001h);
                            side *= 1.0h + (macro - 0.5h) * 2.0h * _DetailMacro;
                        }
                        d += lerp(half3(1, 1, 1) * (half)(w.x + w.z), side, _DetailStrength);
                        if (!top) d += lerp(half3(1, 1, 1) * (half)w.y, SAMPLE_TEXTURE2D(_DetailMap, sampler_DetailMap, p.xz).rgb * (half)w.y / max(_DetailMean.rgb, 0.02h), _DetailStrength);
                    }
                    else d = half3(1, 1, 1) * (half)(w.x + w.z + (top ? 0.0 : w.y));
                    half roof = smoothstep(_RoofAbove - 0.6, _RoofAbove + 0.6, above);
                    float2 tpa = i.positionWS.xz / max(_TopScale, 0.01), tpb = i.positionWS.xz / max(_RoofScale, 0.01);
                    if (top)
                    {   // flat ground and roofs: paving or roofing, seen from above
                        half3 ta = SAMPLE_TEXTURE2D(_TopMap, sampler_DetailMap, tpa).rgb / max(_TopMean.rgb, 0.02h);
                        half3 tb = SAMPLE_TEXTURE2D(_RoofMap, sampler_DetailMap, tpb).rgb / max(_RoofMean.rgb, 0.02h);
                        d += lerp(half3(1, 1, 1), lerp(ta, tb, roof), _TopStrength) * (half)w.y;
                    }
                    // dirt splashed up the foot of the walls, a little soot where they meet the roof line
                    half splash = (1.0h - smoothstep(0.0h, 2.2h, (half)above)) * (1.0h - (half)w.y);
                    d *= 1.0h - _Grime * splash * splash * 0.7h;
                    c.rgb *= clamp(d, 0.0h, 2.5h);
                    if (_DetailNormalStrength > 0.001h || (top && _TopNormalStrength > 0.001h))
                    {
                        // whiteout-blended triplanar normals
                        half3 nx = 0, ny = 0, nz = 0;
                        if (_DetailNormalStrength > 0.001h)
                        {
                            half3 tx = UnpackNormalScale(SAMPLE_TEXTURE2D(_DetailNormal, sampler_DetailNormal, p.zy), _DetailNormalStrength);
                            half3 tz = UnpackNormalScale(SAMPLE_TEXTURE2D(_DetailNormal, sampler_DetailNormal, p.xy), _DetailNormalStrength);
                            nx = half3(0, tx.y, tx.x) * sign(nWS.x);
                            nz = half3(tz.x, tz.y, 0) * sign(nWS.z);
                            if (!top) { half3 ty = UnpackNormalScale(SAMPLE_TEXTURE2D(_DetailNormal, sampler_DetailNormal, p.xz), _DetailNormalStrength); ny = half3(ty.x, 0, ty.y) * sign(nWS.y); }
                        }
                        if (top && _TopNormalStrength > 0.001h)
                        {
                            half3 ta = UnpackNormalScale(SAMPLE_TEXTURE2D(_TopNormal, sampler_DetailNormal, tpa), _TopNormalStrength);
                            half3 tb = UnpackNormalScale(SAMPLE_TEXTURE2D(_RoofNormal, sampler_DetailNormal, tpb), _TopNormalStrength);
                            half3 ty = lerp(ta, tb, roof);
                            ny = half3(ty.x, 0, ty.y) * sign(nWS.y);
                        }
                        nWS = normalize(nWS + nx * w.x + ny * w.y + nz * w.z);
                    }
                }
                else if (_Grime > 0.001h)
                {
                    half splash = (1.0h - smoothstep(0.0h, 2.2h, (half)above)) * (1.0h - saturate(abs((half)nWS.y)));
                    c.rgb *= 1.0h - _Grime * splash * splash * 0.7h;
                }

                InputData input = (InputData)0;
                input.positionWS = i.positionWS;
                input.normalWS = nWS;
                input.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                input.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                input.fogCoord = i.fogCoord;
                input.bakedGI = SampleSH(nWS);
                input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                input.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = c.rgb;
                s.alpha = c.a;
                s.metallic = _Metallic;
                s.smoothness = smooth;
                s.normalTS = half3(0, 0, 1);
                s.occlusion = 1;
                s.emission = _EmissionColor.rgb * SAMPLE_TEXTURE2D(_EmissionMap, sampler_EmissionMap, i.uv).rgb;

                half4 col = UniversalFragmentPBR(input, s);
                col.rgb = MixFog(col.rgb, i.fogCoord);
                return col;
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #pragma multi_compile_instancing
            #include "DawgsLitInput.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(DawgsAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                float3 pws = TransformObjectToWorld(v.positionOS.xyz);
                float3 nws = TransformObjectToWorldNormal(v.normalOS);
                #if defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
                    float3 ld = normalize(_LightPosition - pws);
                #else
                    float3 ld = _LightDirection;
                #endif
                float4 pcs = TransformWorldToHClip(ApplyShadowBias(pws, nws, ld));
                #if UNITY_REVERSED_Z
                    pcs.z = min(pcs.z, UNITY_NEAR_CLIP_VALUE);
                #else
                    pcs.z = max(pcs.z, UNITY_NEAR_CLIP_VALUE);
                #endif
                o.positionCS = pcs;
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.color = v.color;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                if (_Cutoff > 0.001h) clip(DawgsBaseColor(i.uv, i.color).a - _Cutoff);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "DawgsLitInput.hlsl"

            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(DawgsAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.color = v.color;
                return o;
            }

            half frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                if (_Cutoff > 0.001h) clip(DawgsBaseColor(i.uv, i.color).a - _Cutoff);
                return i.positionCS.z;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #pragma multi_compile_instancing
            #include "DawgsLitInput.hlsl"

            struct Varyings { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float2 uv : TEXCOORD1; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(DawgsAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.color = v.color;
                return o;
            }

            half4 frag(Varyings i, bool front : SV_IsFrontFace) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                if (_Cutoff > 0.001h) clip(DawgsBaseColor(i.uv, i.color).a - _Cutoff);
                float3 n = normalize(i.normalWS);
                n = front ? n : -n;
                #if defined(_GBUFFER_NORMALS_OCT)
                    float2 oct = PackNormalOctQuadEncode(n);
                    float2 rm = saturate(oct * 0.5 + 0.5);
                    return half4(PackFloat2To888(rm), 0.0);
                #else
                    return half4(n, 0.0);
                #endif
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
