from html import escape
from typing import Any


def apply_ui_theme(st: Any) -> None:
    """注入 AI PIC 科研工作台的统一视觉主题。"""
    st.markdown(
        """
<style>
:root {
  --pic-bg: #07111f;
  --pic-surface: #0d1b2a;
  --pic-surface-2: #12233a;
  --pic-border: #263955;
  --pic-text: #eaf2ff;
  --pic-muted: #9eb0c9;
  --pic-primary: #60a5fa;
  --pic-primary-strong: #2563eb;
  --pic-accent: #f59e0b;
  --pic-success: #34d399;
  --pic-danger: #f87171;
  --pic-radius: 14px;
}

html, body, [class*="css"] {
  font-family: Inter, "Segoe UI", "Microsoft YaHei", sans-serif;
}

[data-testid="stAppViewContainer"] {
  color: var(--pic-text);
  background:
    radial-gradient(circle at 78% -8%, rgba(37, 99, 235, 0.20), transparent 34rem),
    radial-gradient(circle at 28% 16%, rgba(14, 165, 233, 0.08), transparent 28rem),
    var(--pic-bg);
}

[data-testid="stHeader"] {
  background: rgba(7, 17, 31, 0.82);
  border-bottom: 1px solid rgba(96, 165, 250, 0.12);
  backdrop-filter: blur(12px);
}

[data-testid="stMainBlockContainer"] {
  max-width: 1480px;
  padding: 2rem 2.5rem 5rem;
}

section[data-testid="stSidebar"] {
  width: 340px !important;
  background: linear-gradient(180deg, #0b1728 0%, #091321 100%);
  border-right: 1px solid var(--pic-border);
}

section[data-testid="stSidebar"] > div {
  padding-top: 1rem;
}

h1, h2, h3, h4, h5, h6 {
  color: var(--pic-text);
  letter-spacing: -0.02em;
}

p, label, [data-testid="stCaptionContainer"] {
  line-height: 1.65;
}

.pic-hero {
  position: relative;
  overflow: hidden;
  padding: 2rem 2.2rem;
  margin-bottom: 1rem;
  border: 1px solid rgba(96, 165, 250, 0.24);
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(18, 35, 58, 0.98), rgba(9, 23, 42, 0.94));
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
}

.pic-hero::after {
  content: "";
  position: absolute;
  width: 22rem;
  height: 22rem;
  right: -8rem;
  top: -12rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.30), transparent 68%);
  pointer-events: none;
}

.pic-eyebrow {
  color: #93c5fd;
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.pic-hero h1 {
  max-width: 900px;
  margin: 0.45rem 0 0.55rem;
  font-size: clamp(2rem, 5vw, 3.55rem);
  line-height: 1.05;
}

.pic-hero p {
  max-width: 780px;
  margin: 0;
  color: #bfd0e6;
  font-size: 1.02rem;
}

.pic-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1.25rem;
}

.pic-badge {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0.25rem 0.72rem;
  border: 1px solid var(--pic-border);
  border-radius: 999px;
  color: #dbeafe;
  background: rgba(15, 31, 52, 0.78);
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.78rem;
}

.pic-badge--active {
  border-color: rgba(52, 211, 153, 0.45);
  color: #a7f3d0;
  background: rgba(6, 78, 59, 0.28);
}

.pic-workflow {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 1.25rem;
}

.pic-step {
  min-height: 88px;
  padding: 0.9rem 1rem;
  border: 1px solid var(--pic-border);
  border-radius: var(--pic-radius);
  background: rgba(13, 27, 42, 0.78);
}

.pic-step span {
  color: #93c5fd;
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.72rem;
}

.pic-step strong {
  display: block;
  margin-top: 0.32rem;
  color: var(--pic-text);
  font-size: 0.94rem;
}

.pic-boundary {
  padding: 0.9rem 1rem;
  margin-bottom: 1.4rem;
  border-left: 3px solid var(--pic-accent);
  border-radius: 0 12px 12px 0;
  color: #d4deeb;
  background: rgba(120, 53, 15, 0.17);
}

.pic-sidebar-brand {
  padding: 0.35rem 0 1rem;
}

.pic-sidebar-brand strong {
  display: block;
  color: var(--pic-text);
  font-size: 1.05rem;
}

.pic-sidebar-brand span {
  color: var(--pic-muted);
  font-family: "Fira Code", Consolas, monospace;
  font-size: 0.74rem;
}

div[data-testid="stMetric"] {
  min-height: 116px;
  padding: 1rem 1.05rem;
  border: 1px solid var(--pic-border);
  border-radius: var(--pic-radius);
  background: linear-gradient(145deg, rgba(18, 35, 58, 0.90), rgba(11, 25, 43, 0.90));
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14);
}

div[data-testid="stMetricLabel"] {
  color: var(--pic-muted);
}

div[data-testid="stMetricValue"] {
  color: #f8fbff;
  font-family: "Fira Code", Consolas, monospace;
  font-variant-numeric: tabular-nums;
}

.stButton > button, .stDownloadButton > button {
  min-height: 44px;
  border: 1px solid #355074;
  border-radius: 10px;
  color: #eaf2ff;
  background: #12233a;
  transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--pic-primary);
  color: #ffffff;
  background: #183253;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.14);
}

.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline: 3px solid rgba(96, 165, 250, 0.58);
  outline-offset: 2px;
}

button[kind="primary"] {
  border-color: #3b82f6 !important;
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.26);
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea {
  min-height: 44px;
  border-color: #314766 !important;
  border-radius: 10px !important;
  background: #0a1727 !important;
}

[data-testid="stExpander"] {
  border: 1px solid var(--pic-border);
  border-radius: 12px;
  background: rgba(13, 27, 42, 0.62);
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 0.4rem;
  padding: 0.35rem;
  border: 1px solid var(--pic-border);
  border-radius: 12px;
  background: rgba(13, 27, 42, 0.76);
}

[data-testid="stTabs"] button[role="tab"] {
  min-height: 44px;
  border-radius: 8px;
}

[data-testid="stImage"] img {
  border: 1px solid var(--pic-border);
  border-radius: 12px;
  background: #ffffff;
}

[data-testid="stAlert"] {
  border-radius: 12px;
}

hr {
  border-color: var(--pic-border) !important;
}

@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"] {
    padding: 1rem 1rem 3rem;
  }
  .pic-hero {
    padding: 1.45rem 1.2rem;
  }
  .pic-workflow {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .pic-workflow {
    grid-template-columns: 1fr;
  }
  .pic-step {
    min-height: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_app_hero(st: Any, version: str, description: str) -> None:
    st.markdown(
        f"""
<section class="pic-hero" aria-labelledby="pic-page-title">
  <div class="pic-eyebrow">Photonic design workbench</div>
  <h1 id="pic-page-title">AI PIC Design Studio</h1>
  <p>{escape(description)}。从自然语言规格到模式、优化、传播、端口重叠、版图与报告，保持一次运行可追踪。</p>
  <div class="pic-badges" aria-label="当前能力">
    <span class="pic-badge pic-badge--active">{escape(version)} · DEV ACTIVE</span>
    <span class="pic-badge">SOI · 1×2 MMI</span>
    <span class="pic-badge">2D SCALAR BPM</span>
    <span class="pic-badge">GAUSSIAN MODE OVERLAP</span>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def render_workflow_strip(st: Any) -> None:
    steps = (
        ("01", "解析与校验"),
        ("02", "模式与优化"),
        ("03", "传播与校准"),
        ("04", "版图与交付"),
    )
    cards = "".join(
        f'<div class="pic-step"><span>STAGE {number}</span><strong>{label}</strong></div>'
        for number, label in steps
    )
    st.markdown(
        f'<div class="pic-workflow" aria-label="设计流程">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_model_boundary(st: Any) -> None:
    st.markdown(
        """
<div class="pic-boundary" role="note">
  <strong>模型边界</strong><br>
  当前传播与端口功率来自二维标量 BPM 和简化 Gaussian 模式投影，适合趋势验证与工程演示；不是严格全矢量本征模式或 S 参数签核结果。
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar_brand(st: Any, version: str) -> None:
    st.markdown(
        f"""
<div class="pic-sidebar-brand">
  <strong>Design Console</strong>
  <span>{escape(version)} · PARAMETER WORKSPACE</span>
</div>
""",
        unsafe_allow_html=True,
    )
