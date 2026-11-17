// Dawgs Uprising -> Unity: trees, bushes and grass made in Blender (DawgsRig/du_env.py).
//   colour      vertex colours (Cycles-baked AO already in them) x Base Color (the per-instance tint variants)
//   wind        vertex alpha is how free a vertex is to move (0 at the trunk / blade root, 1 at the tips): a slow sway
//               phased by each plant's position, gusts rolling across the map, and a quick leaf flutter
//   lighting    URP PBR on the canopy-bent normals (both faces share them, so a canopy shades as one soft volume),
//               plus a little sunlight glowing through the leaves when you look towards the sun
//   LOD         LODGroup cross-fades are dithered
Shader "Dawgs/Foliage"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1,1,1,1)
        _Smoothness ("Smoothness", Range(0,1)) = 0.12
        _Translucency ("Translucency", Range(0,2)) = 0.45
        _WindStrength ("Wind Strength (m at the tips)", Float) = 0.12
        _WindSpeed ("Wind Speed", Float) = 1.1
        _WindFlutter ("Leaf Flutter", Range(0,1)) = 0.35
        _WindDir ("Wind Direction (xz)", Vector) = (0.8, 0, 0.6, 0)
        _GustScale ("Gust Size (m)", Float) = 60
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 0
    }

    HLSLINCLUDE
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

    CBUFFER_START(UnityPerMaterial)
        half4  _BaseColor;
        half   _Smoothness;
        half   _Translucency;
        float  _WindStrength;
        float  _WindSpeed;
        half   _WindFlutter;
        float4 _WindDir;
        float  _GustScale;
    CBUFFER_END

    struct FoliageAttributes
    {
        float4 positionOS : POSITION;
        float3 normalOS   : NORMAL;
        half4  color      : COLOR;
        UNITY_VERTEX_INPUT_INSTANCE_ID
    };

    // world-space wind offset for a vertex (same in every pass, so shadows and depth sway with the colour)
    float3 DawgsWind(float3 posWS, half weight)
    {
        float3 pivot = TransformObjectToWorld(float3(0, 0, 0));
        float t = _Time.y * _WindSpeed;
        float2 dir = normalize(_WindDir.xz + 1e-4);
        float along = dot(pivot.xz, dir) / max(_GustScale, 1.0);
        float gust = 0.55 + 0.45 * sin(t * 0.55 - along * 6.2832) * sin(t * 0.21 + along * 2.1 + 1.3);
        float phase = dot(pivot.xz, float2(0.173, 0.091));
        float sway = sin(t + phase) * 0.7 + sin(t * 2.31 + phase * 1.7) * 0.3;
        float flutter = sin(t * 7.3 + dot(posWS, float3(3.1, 2.3, 2.7))) * _WindFlutter;
        float w = weight * weight;
        float3 off = float3(dir.x, 0, dir.y) * (gust * 0.6 + sway * 0.4 * gust) * _WindStrength * w;
        off += float3(0.7, 0.35, 0.6) * flutter * _WindStrength * 0.25 * weight;
        off.y -= length(off.xz) * 0.15;            // bending also lowers the tip a little
        return off;
    }
    ENDHLSL

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
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
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #if defined(LOD_FADE_CROSSFADE)
                #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/LODCrossFade.hlsl"
            #endif

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                half4  color      : COLOR;
                half   fogCoord   : TEXCOORD2;
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(FoliageAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                float3 pws = TransformObjectToWorld(v.positionOS.xyz);
                pws += DawgsWind(pws, v.color.a);
                o.positionWS = pws;
                o.positionCS = TransformWorldToHClip(pws);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.color = v.color;
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                #if defined(LOD_FADE_CROSSFADE)
                    LODFadeCrossFade(i.positionCS);
                #endif
                half3 albedo = i.color.rgb * _BaseColor.rgb;
                float3 nWS = normalize(i.normalWS);

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
                s.albedo = albedo;
                s.alpha = 1;
                s.metallic = 0;
                s.smoothness = _Smoothness;
                s.specular = half3(0.04, 0.04, 0.04);
                s.normalTS = half3(0, 0, 1);
                s.occlusion = 1;

                half4 col = UniversalFragmentPBR(input, s);

                // sunlight through the leaves
                Light sun = GetMainLight(input.shadowCoord, i.positionWS, input.shadowMask);
                half back = pow(saturate(dot(input.viewDirectionWS, -sun.direction)), 4.0h);
                half wrap = saturate(dot(-nWS, sun.direction) * 0.5h + 0.5h);
                col.rgb += albedo * sun.color * sun.shadowAttenuation * back * wrap * _Translucency;

                col.rgb = MixFog(col.rgb, i.fogCoord);
                return half4(col.rgb, 1);
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
            Cull Off

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            #if defined(LOD_FADE_CROSSFADE)
                #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/LODCrossFade.hlsl"
            #endif

            float3 _LightDirection;
            float3 _LightPosition;

            struct Varyings { float4 positionCS : SV_POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(FoliageAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                float3 pws = TransformObjectToWorld(v.positionOS.xyz);
                pws += DawgsWind(pws, v.color.a);
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
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                #if defined(LOD_FADE_CROSSFADE)
                    LODFadeCrossFade(i.positionCS);
                #endif
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
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_instancing
            #if defined(LOD_FADE_CROSSFADE)
                #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/LODCrossFade.hlsl"
            #endif

            struct Varyings { float4 positionCS : SV_POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(FoliageAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                float3 pws = TransformObjectToWorld(v.positionOS.xyz);
                pws += DawgsWind(pws, v.color.a);
                o.positionCS = TransformWorldToHClip(pws);
                return o;
            }

            half frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                #if defined(LOD_FADE_CROSSFADE)
                    LODFadeCrossFade(i.positionCS);
                #endif
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
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_instancing
            #if defined(LOD_FADE_CROSSFADE)
                #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/LODCrossFade.hlsl"
            #endif

            struct Varyings { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };

            Varyings vert(FoliageAttributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                float3 pws = TransformObjectToWorld(v.positionOS.xyz);
                pws += DawgsWind(pws, v.color.a);
                o.positionCS = TransformWorldToHClip(pws);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                #if defined(LOD_FADE_CROSSFADE)
                    LODFadeCrossFade(i.positionCS);
                #endif
                float3 n = normalize(i.normalWS);
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
