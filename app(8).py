import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

try:
    import plotly.express as px
    import plotly.graph_objects as go
except Exception:
    px = None
    go = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

st.set_page_config(
    page_title="VisionIQ | Business Visual Intelligence",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.hero {
    padding: 1.4rem 1.6rem;
    border-radius: 24px;
    background: linear-gradient(135deg, #101828 0%, #344054 55%, #6941C6 100%);
    color: white;
    margin-bottom: 1rem;
}
.hero h1 {font-size: 2.65rem; font-weight: 850; margin: 0; letter-spacing: -0.04em;}
.hero p {font-size: 1.05rem; color: #EAECF0; max-width: 980px; margin-top: .55rem;}
.small-muted {color:#667085; font-size:.92rem;}
.card {
    border: 1px solid #EAECF0;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    background: #FFFFFF;
    box-shadow: 0 8px 24px rgba(16,24,40,.05);
    margin-bottom: .8rem;
}
.executive {
    border-left: 6px solid #7F56D9;
    background: #F9F5FF;
    border-radius: 16px;
    padding: 1rem 1.15rem;
    color:#101828;
}
.recommend {
    border-left: 5px solid #12B76A;
    background: #ECFDF3;
    border-radius: 14px;
    padding: .8rem 1rem;
    margin: .45rem 0;
    color:#101828;
}
.warning-note {
    border-left: 5px solid #F79009;
    background: #FFFAEB;
    border-radius: 14px;
    padding: .8rem 1rem;
    margin: .45rem 0;
    color:#101828;
}
.tag {
    display:inline-block;
    padding:.28rem .65rem;
    margin:.18rem .14rem;
    border-radius:999px;
    background:#EEF4FF;
    color:#3538CD!important;
    font-weight:700;
    font-size:.82rem;
}
.good {color:#027A48; font-weight:700;}
.mid {color:#B54708; font-weight:700;}
.low {color:#B42318; font-weight:700;}
</style>
""",
    unsafe_allow_html=True,
)

FALLBACK: Dict[str, Any] = {
    "executive_summary": "Upload an image and run analysis to generate a business-focused visual intelligence report.",
    "caption": "No caption generated yet.",
    "image_type": "Other",
    "business_use_case": "General visual review",
    "scene_summary": "No scene summary generated yet.",
    "detected_objects": [],
    "brand_analysis": {
        "visible_brands": [],
        "logo_visibility": "Unknown",
        "detected_text": [],
        "brand_prominence": 0,
        "packaging_clarity": 0,
        "notes": "No brand analysis available yet.",
    },
    "marketing_scores": {
        "product_visibility": 0,
        "branding_clarity": 0,
        "social_media_appeal": 0,
        "visual_cleanliness": 0,
        "campaign_readiness": 0,
        "engagement_potential": 0,
    },
    "audience_prediction": {
        "primary_group": "Unknown",
        "age_range": "Unknown",
        "customer_intent": "Unknown",
        "reasoning": "No audience prediction available yet.",
    },
    "channel_fit": [],
    "business_kpis": {
        "people_count_estimate": 0,
        "product_count_estimate": 0,
        "brand_mentions_count": 0,
        "visual_clutter_level": "Unknown",
        "dominant_emotion_or_mood": "Unknown",
        "product_focus_level": "Unknown",
    },
    "marketing_insights": [],
    "campaign_recommendations": [],
    "optimization_suggestions": [],
    "risks_or_notes": [],
    "tags": [],
    "overall_confidence": 0,
}

SCHEMA = """
Return ONLY valid JSON with this exact structure:
{
  "executive_summary": "2-3 sentence C-suite friendly summary of business value and best use",
  "caption": "one sentence visual caption",
  "image_type": "Product | Lifestyle | Event | Retail | Social Content | Food | Real Estate | Other",
  "business_use_case": "best business use for this image",
  "scene_summary": "2-3 sentence business-friendly visual summary",
  "detected_objects": [
    {"label":"object/entity", "confidence":0-100, "evidence":"visual cue", "bbox":[x_min,y_min,x_max,y_max]}
  ],
  "brand_analysis": {
    "visible_brands": ["brand names if visible"],
    "logo_visibility": "High | Medium | Low | None | Unknown",
    "detected_text": ["visible text if readable"],
    "brand_prominence": 0-100,
    "packaging_clarity": 0-100,
    "notes": "brand or logo observations"
  },
  "marketing_scores": {
    "product_visibility": 0-100,
    "branding_clarity": 0-100,
    "social_media_appeal": 0-100,
    "visual_cleanliness": 0-100,
    "campaign_readiness": 0-100,
    "engagement_potential": 0-100
  },
  "audience_prediction": {
    "primary_group":"likely target audience",
    "age_range":"likely age range or Unknown",
    "customer_intent":"Awareness | Consideration | Conversion | Retention | Unknown",
    "reasoning":"why this audience/intention fits"
  },
  "channel_fit": [
    {"channel":"Instagram Ads | TikTok/Reels | Ecommerce PDP | Email Banner | Website Hero | Retail Audit | Event Recap | Other", "fit_score":0-100, "reason":"why"}
  ],
  "business_kpis": {
    "people_count_estimate": 0,
    "product_count_estimate": 0,
    "brand_mentions_count": 0,
    "visual_clutter_level": "Low | Medium | High | Unknown",
    "dominant_emotion_or_mood": "mood",
    "product_focus_level": "Low | Medium | High | Unknown"
  },
  "marketing_insights": [
    {"insight":"what this suggests", "why_it_matters":"business value"}
  ],
  "campaign_recommendations": [
    {"recommendation":"specific action", "team":"Marketing | Product | Retail | Social | Events | Creative | Ecommerce"}
  ],
  "optimization_suggestions": ["specific visual or campaign improvements"],
  "risks_or_notes": ["limitations or ambiguity"],
  "tags": ["short searchable tags"],
  "overall_confidence": 0-100
}
For bbox, use normalized coordinates from 0 to 1000. If unsure, use null.
Confidence scores should reflect visual evidence and business readiness, not hidden model probability.
"""


def get_secret_key() -> Optional[str]:
    try:
        if st.secrets.get("GEMINI_API_KEY"):
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


def sidebar_api_key() -> Optional[str]:
    key = get_secret_key()
    if key:
        return key
    return st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        help="For local testing only. On Streamlit Cloud, add GEMINI_API_KEY under App settings → Secrets.",
    )


def clean_json_text(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
    if t.lower().startswith("json"):
        t = t[4:].strip()
    return t


def parse_json(text: str) -> Dict[str, Any]:
    t = clean_json_text(text)
    if not t:
        return FALLBACK.copy()
    try:
        return json.loads(t)
    except Exception:
        start, end = t.find("{"), t.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(t[start : end + 1])
            except Exception:
                pass
    out = FALLBACK.copy()
    out["scene_summary"] = t[:1200]
    out["risks_or_notes"] = ["Model returned non-JSON text; showing fallback summary."]
    return out


def ensure_score(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except Exception:
        return 0


def normalize(result: Dict[str, Any]) -> Dict[str, Any]:
    out = json.loads(json.dumps(FALLBACK))
    if isinstance(result, dict):
        out.update(result)

    for key in ["detected_objects", "channel_fit", "marketing_insights", "campaign_recommendations", "optimization_suggestions", "risks_or_notes", "tags"]:
        if not isinstance(out.get(key), list):
            out[key] = []

    if not isinstance(out.get("brand_analysis"), dict):
        out["brand_analysis"] = FALLBACK["brand_analysis"].copy()
    if not isinstance(out.get("marketing_scores"), dict):
        out["marketing_scores"] = FALLBACK["marketing_scores"].copy()
    if not isinstance(out.get("audience_prediction"), dict):
        out["audience_prediction"] = FALLBACK["audience_prediction"].copy()
    if not isinstance(out.get("business_kpis"), dict):
        out["business_kpis"] = FALLBACK["business_kpis"].copy()

    for key in FALLBACK["marketing_scores"]:
        out["marketing_scores"][key] = ensure_score(out["marketing_scores"].get(key, 0))
    out["brand_analysis"]["brand_prominence"] = ensure_score(out["brand_analysis"].get("brand_prominence", 0))
    out["brand_analysis"]["packaging_clarity"] = ensure_score(out["brand_analysis"].get("packaging_clarity", 0))
    out["overall_confidence"] = ensure_score(out.get("overall_confidence", 0))

    return out


def analyze_image(image_bytes: bytes, mime: str, model: str, business_mode: str, detail: str, key: str) -> Dict[str, Any]:
    if genai is None or types is None:
        raise RuntimeError("Missing google-genai. Run: pip install -r requirements.txt")

    client = genai.Client(api_key=key)
    prompt = f"""You are VisionIQ, an AI visual intelligence analyst for business teams.
Analyze the uploaded image as a product and business-focused visual asset.
Business mode: {business_mode}
Detail level: {detail}

Focus on:
- business value, not just object detection
- brand visibility, logo/text clarity, product placement, audience, and channel fit
- campaign readiness and specific optimization suggestions
- marketing, ecommerce, retail, or social media use cases

{SCHEMA}
"""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime)
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return normalize(parse_json(response.text))


def draw_boxes(img: Image.Image, objects: List[Dict[str, Any]]) -> Image.Image:
    out = img.copy().convert("RGB")
    draw = ImageDraw.Draw(out)
    width, height = out.size

    for i, obj in enumerate(objects[:12], start=1):
        box = obj.get("bbox")
        label = str(obj.get("label", f"object {i}"))[:28]
        if not isinstance(box, list) or len(box) != 4:
            continue
        try:
            x1, y1, x2, y2 = [float(v) for v in box]
        except Exception:
            continue
        x1, y1, x2, y2 = int(x1 / 1000 * width), int(y1 / 1000 * height), int(x2 / 1000 * width), int(y2 / 1000 * height)
        if x2 <= x1 or y2 <= y1:
            continue
        draw.rectangle([x1, y1, x2, y2], outline="yellow", width=max(3, width // 260))
        draw.rectangle([x1, max(0, y1 - 26), x1 + min(250, 18 + len(label) * 8), y1], fill="yellow")
        draw.text((x1 + 6, max(0, y1 - 21)), f"{i}. {label}", fill="black")
    return out


def score_label(score: int) -> str:
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Moderate"
    return "Needs work"


def score_cards(scores: Dict[str, Any]) -> None:
    cols = st.columns(3)
    labels = {
        "product_visibility": "Product Visibility",
        "branding_clarity": "Branding Clarity",
        "social_media_appeal": "Social Appeal",
        "visual_cleanliness": "Visual Cleanliness",
        "campaign_readiness": "Campaign Readiness",
        "engagement_potential": "Engagement Potential",
    }
    for idx, (key, label) in enumerate(labels.items()):
        score = ensure_score(scores.get(key, 0))
        with cols[idx % 3]:
            st.metric(label, f"{score}%", score_label(score))
            st.progress(score / 100)


def plot_score_chart(scores: Dict[str, Any]) -> None:
    if px is None:
        return
    df = pd.DataFrame(
        [{"Metric": k.replace("_", " ").title(), "Score": ensure_score(v)} for k, v in scores.items()]
    )
    fig = px.bar(df, x="Metric", y="Score", range_y=[0, 100], text="Score", title="Marketing Readiness Scorecard")
    fig.update_layout(height=420, xaxis_title=None, yaxis_title="Score")
    st.plotly_chart(fig, use_container_width=True)


def plot_channel_fit(channel_fit: List[Dict[str, Any]]) -> None:
    if px is None or not channel_fit:
        return
    df = pd.DataFrame(channel_fit)
    if "fit_score" not in df.columns or "channel" not in df.columns:
        return
    df["fit_score"] = df["fit_score"].apply(ensure_score)
    fig = px.bar(df, x="fit_score", y="channel", orientation="h", range_x=[0, 100], text="fit_score", title="Best Channel Fit")
    fig.update_layout(height=380, xaxis_title="Fit Score", yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)


def render_tags(tags: List[str]) -> None:
    if tags:
        st.markdown(" ".join([f"<span class='tag'>{tag}</span>" for tag in tags[:18]]), unsafe_allow_html=True)


def display_result(result: Dict[str, Any], img: Image.Image) -> None:
    st.markdown(f"<div class='executive'><b>Executive Summary</b><br>{result.get('executive_summary', '')}</div>", unsafe_allow_html=True)
    st.write("")

    top = st.columns([1.5, 1, 1, 1])
    top[0].success(result.get("caption", ""))
    top[1].metric("Image Type", result.get("image_type", "Other"))
    top[2].metric("Business Use", result.get("business_use_case", "General"))
    top[3].metric("Overall Confidence", f"{result.get('overall_confidence', 0)}%")

    tab_dash, tab_brand, tab_channels, tab_objects, tab_recs, tab_export = st.tabs(
        ["📊 Business Dashboard", "🏷️ Brand Analytics", "📣 Channel Fit", "🔎 Visual Evidence", "✅ Recommendations", "⬇️ Export"]
    )

    with tab_dash:
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Marketing Scorecards")
            score_cards(result.get("marketing_scores", {}))
        with right:
            st.subheader("Business KPIs")
            kpi = result.get("business_kpis", {})
            k1, k2, k3 = st.columns(3)
            k1.metric("People", kpi.get("people_count_estimate", 0))
            k2.metric("Products", kpi.get("product_count_estimate", 0))
            k3.metric("Brand Mentions", kpi.get("brand_mentions_count", 0))
            st.write(f"**Visual clutter:** {kpi.get('visual_clutter_level', 'Unknown')}")
            st.write(f"**Mood:** {kpi.get('dominant_emotion_or_mood', 'Unknown')}")
            st.write(f"**Product focus:** {kpi.get('product_focus_level', 'Unknown')}")
            st.write(f"**Audience:** {result.get('audience_prediction', {}).get('primary_group', 'Unknown')}")
            st.write(f"**Customer intent:** {result.get('audience_prediction', {}).get('customer_intent', 'Unknown')}")
        plot_score_chart(result.get("marketing_scores", {}))
        st.subheader("Scene Summary")
        st.write(result.get("scene_summary", ""))
        render_tags(result.get("tags", []))

    with tab_brand:
        brand = result.get("brand_analysis", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Logo Visibility", brand.get("logo_visibility", "Unknown"))
        c2.metric("Brand Prominence", f"{ensure_score(brand.get('brand_prominence', 0))}%")
        c3.metric("Packaging Clarity", f"{ensure_score(brand.get('packaging_clarity', 0))}%")
        c4.metric("Brands Found", len(brand.get("visible_brands", []) or []))
        st.write("**Visible brands:**", ", ".join(brand.get("visible_brands", []) or []) or "None detected")
        st.write("**Detected text:**", ", ".join(brand.get("detected_text", []) or []) or "None detected")
        st.write("**Brand notes:**", brand.get("notes", ""))
        audience = result.get("audience_prediction", {})
        st.subheader("Audience Prediction")
        st.write(f"**Primary group:** {audience.get('primary_group', 'Unknown')}")
        st.write(f"**Age range:** {audience.get('age_range', 'Unknown')}")
        st.write(f"**Reasoning:** {audience.get('reasoning', '')}")

    with tab_channels:
        channel_fit = result.get("channel_fit", [])
        if channel_fit:
            plot_channel_fit(channel_fit)
            st.dataframe(pd.DataFrame(channel_fit), use_container_width=True, hide_index=True)
        else:
            st.info("No channel fit generated.")

    with tab_objects:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.image(draw_boxes(img, result.get("detected_objects", [])), caption="AI-estimated visual evidence boxes", use_container_width=True)
        with c2:
            objects = result.get("detected_objects", [])
            if objects:
                df = pd.DataFrame(objects)
                if "bbox" in df.columns:
                    df["bbox"] = df["bbox"].apply(lambda x: "—" if x is None else str(x))
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No objects detected.")

    with tab_recs:
        st.subheader("Business Insights")
        for item in result.get("marketing_insights", []):
            st.markdown(
                f"<div class='card'><b>{item.get('insight', '')}</b><br><span class='small-muted'>{item.get('why_it_matters', '')}</span></div>",
                unsafe_allow_html=True,
            )
        st.subheader("Campaign Recommendations")
        for item in result.get("campaign_recommendations", []):
            st.markdown(
                f"<div class='recommend'><b>{item.get('team', 'Team')}:</b> {item.get('recommendation', '')}</div>",
                unsafe_allow_html=True,
            )
        st.subheader("Optimization Suggestions")
        for suggestion in result.get("optimization_suggestions", []):
            st.write(f"• {suggestion}")
        for note in result.get("risks_or_notes", []):
            st.markdown(f"<div class='warning-note'>{note}</div>", unsafe_allow_html=True)

    with tab_export:
        st.json(result)


def comparison_dashboard(all_results: List[Dict[str, Any]]) -> None:
    st.subheader("Portfolio Comparison Dashboard")
    rows = []
    for item in all_results:
        analysis = item["analysis"]
        scores = analysis.get("marketing_scores", {})
        rows.append(
            {
                "image": item["file_name"],
                "type": analysis.get("image_type"),
                "business_use_case": analysis.get("business_use_case"),
                "campaign_readiness": ensure_score(scores.get("campaign_readiness", 0)),
                "social_media_appeal": ensure_score(scores.get("social_media_appeal", 0)),
                "branding_clarity": ensure_score(scores.get("branding_clarity", 0)),
                "product_visibility": ensure_score(scores.get("product_visibility", 0)),
                "overall_confidence": ensure_score(analysis.get("overall_confidence", 0)),
                "top_tags": ", ".join(analysis.get("tags", [])[:5]),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if px is not None and not df.empty:
        fig = px.scatter(
            df,
            x="campaign_readiness",
            y="social_media_appeal",
            size="product_visibility",
            hover_name="image",
            hover_data=["type", "business_use_case", "branding_clarity"],
            range_x=[0, 100],
            range_y=[0, 100],
            title="Campaign Readiness vs. Social Media Appeal",
        )
        fig.update_layout(height=470)
        st.plotly_chart(fig, use_container_width=True)

        best = df.sort_values(["campaign_readiness", "social_media_appeal"], ascending=False).head(1)
        if not best.empty:
            st.success(f"Best overall business asset: {best.iloc[0]['image']}")


def main() -> None:
    st.markdown(
        """
<div class="hero">
  <h1>VisionIQ</h1>
  <p>AI-powered visual intelligence for marketing, retail, ecommerce, and social media teams. Upload business images and get campaign-readiness scores, brand analysis, audience prediction, channel fit, and executive-ready recommendations.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Product Setup")
        key = sidebar_api_key()
        model = st.selectbox("Gemini model", ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview"], index=0)
        business_mode = st.selectbox(
            "Business mode",
            [
                "Marketing Campaign Review",
                "Ecommerce Product Optimization",
                "Retail Shelf Intelligence",
                "Social Media Creative Strategy",
                "Event Activation Analysis",
                "Brand Visibility Audit",
            ],
        )
        detail = st.radio("Report depth", ["Executive", "Balanced", "Detailed"], index=1)
        st.caption("Tip: Add GEMINI_API_KEY in Streamlit Cloud secrets for deployment.")

    files = st.file_uploader(
        "Upload one or more product, retail, event, or campaign images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if not files:
        c1, c2, c3 = st.columns(3)
        c1.info("📦 Product images → product visibility and ecommerce readiness")
        c2.info("🏬 Retail images → shelf clarity and brand presence")
        c3.info("📱 Social images → engagement potential and channel fit")
        return

    if not key:
        st.warning("Add your Gemini API key in the sidebar or Streamlit secrets before running analysis.")
        return

    if st.button("Generate Business Intelligence Report", type="primary", use_container_width=True):
        all_results = []
        for uploaded in files:
            image_bytes = uploaded.getvalue()
            img = Image.open(io.BytesIO(image_bytes))
            with st.spinner(f"Analyzing {uploaded.name} as a business visual asset..."):
                try:
                    result = analyze_image(image_bytes, uploaded.type or "image/jpeg", model, business_mode, detail, key)
                except Exception as exc:
                    st.error(f"Analysis failed for {uploaded.name}: {exc}")
                    result = json.loads(json.dumps(FALLBACK))
                    result["risks_or_notes"] = [str(exc)]

            all_results.append({"file_name": uploaded.name, "analysis": result})
            with st.expander(f"Business Report: {uploaded.name}", expanded=True):
                col_img, col_report = st.columns([0.85, 1.55])
                with col_img:
                    st.image(img, caption=uploaded.name, use_container_width=True)
                with col_report:
                    display_result(result, img)

        if len(all_results) > 1:
            comparison_dashboard(all_results)

        export = {
            "product": "VisionIQ",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "business_mode": business_mode,
            "results": all_results,
        }
        st.download_button(
            "Download Business Intelligence JSON",
            data=json.dumps(export, indent=2),
            file_name="visioniq_business_report.json",
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
