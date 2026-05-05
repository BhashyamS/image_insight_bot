import io, json, os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

st.set_page_config(page_title="Image Insight Bot", page_icon="🖼️", layout="wide")

st.markdown("""
<style>
.main-title{font-size:2.4rem;font-weight:800;margin-bottom:.1rem}.muted{color:#667085}.tag{display:inline-block;padding:.25rem .6rem;margin:.15rem;border-radius:999px;background:#EEF4FF;color:#3538CD;font-weight:650;font-size:.82rem}.insight{border-left:4px solid #7F56D9;background:#F9F5FF;padding:.8rem 1rem;border-radius:12px;margin:.5rem 0}.note{border-left:4px solid #F79009;background:#FFFAEB;padding:.8rem 1rem;border-radius:12px;margin:.5rem 0}
</style>
""", unsafe_allow_html=True)

FALLBACK = {
    "caption":"No result generated yet.","image_type":"Other","scene_summary":"Upload an image and run analysis.",
    "detected_objects":[],"visual_elements":{"dominant_colors":[],"setting":"unknown","people_present":False,"brand_or_text_visible":"none"},
    "marketing_insights":[],"campaign_recommendations":[],"risks_or_notes":[],"tags":[],"overall_confidence":0
}

SCHEMA = """
Return ONLY valid JSON with this exact structure:
{
 "caption":"one sentence caption",
 "image_type":"Product | Lifestyle | Event | Retail | Social Content | Other",
 "scene_summary":"2-3 sentence business-friendly summary",
 "detected_objects":[{"label":"object/entity","confidence":0-100,"evidence":"visual cue","bbox":[x_min,y_min,x_max,y_max]}],
 "visual_elements":{"dominant_colors":["colors"],"setting":"setting","people_present":true/false,"brand_or_text_visible":"text or none"},
 "marketing_insights":[{"insight":"what this suggests","why_it_matters":"business value"}],
 "campaign_recommendations":[{"recommendation":"actionable idea","team":"Marketing | Product | Retail | Social | Events"}],
 "risks_or_notes":["limitations or ambiguity"],
 "tags":["short tags"],
 "overall_confidence":0-100
}
For bbox, use normalized coordinates from 0 to 1000. If unsure, use null.
"""

def api_key() -> Optional[str]:
    try:
        if st.secrets.get("GEMINI_API_KEY"):
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    return st.sidebar.text_input("Gemini API Key", type="password", help="For local testing only. On Streamlit Cloud, add this under App settings → Secrets.")

def parse_json(text: str) -> Dict[str, Any]:
    if not text:
        return FALLBACK.copy()
    t = text.strip().strip("`").replace("json\n", "", 1).replace("JSON\n", "", 1)
    try:
        return json.loads(t)
    except Exception:
        s, e = t.find("{"), t.rfind("}")
        if s >= 0 and e > s:
            try:
                return json.loads(t[s:e+1])
            except Exception:
                pass
    out = FALLBACK.copy(); out["scene_summary"] = t[:1200]; out["risks_or_notes"] = ["Model returned non-JSON text; showing fallback summary."]
    return out

def normalize(r: Dict[str, Any]) -> Dict[str, Any]:
    out = FALLBACK.copy(); out.update(r or {})
    for k in ["detected_objects","marketing_insights","campaign_recommendations","risks_or_notes","tags"]:
        if not isinstance(out.get(k), list): out[k] = []
    if not isinstance(out.get("visual_elements"), dict): out["visual_elements"] = FALLBACK["visual_elements"]
    try: out["overall_confidence"] = int(float(out.get("overall_confidence",0)))
    except Exception: out["overall_confidence"] = 0
    return out

def analyze(image_bytes: bytes, mime: str, model: str, lens: str, detail: str, key: str) -> Dict[str, Any]:
    if genai is None or types is None:
        raise RuntimeError("Missing google-genai. Run: pip install -r requirements.txt")
    client = genai.Client(api_key=key)
    prompt = f"""You are an AI Image Insight Bot for a marketing analytics team.
Analyze this image through a {lens} lens. Detail level: {detail}.
Generate captioning, object/entity detection, image type classification, confidence-style scores, and actionable business recommendations.
Confidence scores should reflect visual clarity and evidence, not hidden probabilities.
{SCHEMA}"""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime)
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return normalize(parse_json(response.text))

def draw_boxes(img: Image.Image, objects: List[Dict[str, Any]]) -> Image.Image:
    out = img.copy().convert("RGB"); draw = ImageDraw.Draw(out); w,h = out.size
    for i, obj in enumerate(objects[:12], start=1):
        box = obj.get("bbox"); label = str(obj.get("label", f"object {i}"))[:26]
        if not isinstance(box, list) or len(box) != 4: continue
        try: x1,y1,x2,y2 = [float(v) for v in box]
        except Exception: continue
        x1,y1,x2,y2 = int(x1/1000*w), int(y1/1000*h), int(x2/1000*w), int(y2/1000*h)
        if x2 <= x1 or y2 <= y1: continue
        draw.rectangle([x1,y1,x2,y2], outline="yellow", width=max(3,w//250))
        draw.rectangle([x1, max(0,y1-24), x1+min(220, 14+len(label)*8), y1], fill="yellow")
        draw.text((x1+5, max(0,y1-20)), f"{i}. {label}", fill="black")
    return out

def display_result(result: Dict[str, Any], img: Image.Image):
    c1,c2,c3 = st.columns([2,1,1])
    c1.success(result.get("caption", "")); c2.metric("Image Type", result.get("image_type","Other")); c3.metric("Confidence", f"{result.get('overall_confidence',0)}%")
    overview, objects, insights, export = st.tabs(["Overview","Detected Objects","Business Insights","Export"])
    with overview:
        left,right = st.columns([1.1,1])
        with left:
            st.subheader("Scene Summary"); st.write(result.get("scene_summary",""))
            v = result.get("visual_elements", {})
            st.write(f"**Setting:** {v.get('setting','unknown')}")
            st.write(f"**People present:** {v.get('people_present', False)}")
            st.write(f"**Brand/text visible:** {v.get('brand_or_text_visible','none')}")
            colors = v.get("dominant_colors", [])
            if colors: st.markdown(" ".join([f"<span class='tag'>{x}</span>" for x in colors]), unsafe_allow_html=True)
        with right:
            st.subheader("Annotated View"); st.image(draw_boxes(img, result.get("detected_objects", [])), use_container_width=True); st.caption("Boxes are AI-estimated visual markers for explainability.")
    with objects:
        if result.get("detected_objects"):
            df = pd.DataFrame(result["detected_objects"])
            if "bbox" in df: df["bbox"] = df["bbox"].apply(lambda x: "—" if x is None else str(x))
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: st.info("No objects detected.")
    with insights:
        st.subheader("Marketing Insights")
        for item in result.get("marketing_insights", []):
            st.markdown(f"<div class='insight'><b>{item.get('insight','')}</b><br>{item.get('why_it_matters','')}</div>", unsafe_allow_html=True)
        st.subheader("Recommended Actions")
        for item in result.get("campaign_recommendations", []):
            st.markdown(f"<div class='insight'><b>{item.get('team','Team')}:</b> {item.get('recommendation','')}</div>", unsafe_allow_html=True)
        for note in result.get("risks_or_notes", []):
            st.markdown(f"<div class='note'>{note}</div>", unsafe_allow_html=True)
        if result.get("tags"):
            st.markdown(" ".join([f"<span class='tag'>{x}</span>" for x in result["tags"]]), unsafe_allow_html=True)
    with export:
        st.json(result)

def main():
    st.markdown("<div class='main-title'>Image Insight Bot</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Upload product, retail, event, or campaign images to generate captions, detected objects, confidence scores, and business recommendations.</div>", unsafe_allow_html=True)
    st.divider()
    with st.sidebar:
        st.header("Setup")
        key = api_key()
        model = st.selectbox("Gemini model", ["gemini-2.5-flash","gemini-2.0-flash","gemini-3-flash-preview"], index=0)
        lens = st.selectbox("Business lens", ["Marketing Analytics","Retail Merchandising","Product Marketing","Event Activation","Social Media Campaign"])
        detail = st.radio("Detail level", ["Concise","Balanced","Detailed"], index=1)
    files = st.file_uploader("Upload one or more images", type=["png","jpg","jpeg"], accept_multiple_files=True)
    if not files:
        st.info("Upload a PNG, JPG, or JPEG image to start.")
        return
    if not key:
        st.warning("Add your Gemini API key in the sidebar or Streamlit secrets before running analysis.")
        return
    if st.button("Analyze Image(s)", type="primary", use_container_width=True):
        all_results = []
        for f in files:
            img_bytes = f.getvalue(); img = Image.open(io.BytesIO(img_bytes))
            with st.spinner(f"Analyzing {f.name}..."):
                try: result = analyze(img_bytes, f.type or "image/jpeg", model, lens, detail, key)
                except Exception as e:
                    st.error(f"Analysis failed for {f.name}: {e}"); result = FALLBACK.copy(); result["risks_or_notes"]=[str(e)]
            all_results.append({"file_name": f.name, "analysis": result})
            with st.expander(f"Results: {f.name}", expanded=True):
                a,b = st.columns([.85,1.45]); a.image(img, caption=f.name, use_container_width=True)
                with b: display_result(result, img)
        if len(all_results) > 1:
            st.subheader("Batch Comparison Summary")
            rows = [{"image":x["file_name"],"type":x["analysis"].get("image_type"),"confidence":x["analysis"].get("overall_confidence"),"object_count":len(x["analysis"].get("detected_objects",[])),"top_tags":", ".join(x["analysis"].get("tags",[])[:5])} for x in all_results]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        export = {"app_name":"Image Insight Bot","generated_at":datetime.utcnow().isoformat()+"Z","results":all_results}
        st.download_button("Download analysis JSON", data=json.dumps(export, indent=2), file_name="image_insight_results.json", mime="application/json", use_container_width=True)

if __name__ == "__main__":
    main()
