BASE_CSS = r"""
/* Force base text color for widgets (prevents invisible text if theme breaks) */
.stApp, .stApp * {
  color: #0b1c30;
}

/* Fix Streamlit default chrome (keep header for sidebar toggle) */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Hide Streamlit multipage default nav (we render our own) */
div[data-testid="stSidebarNav"] { display: none !important; }

/* Hide the collapse sidebar text if Streamlit tries to render it without font */
button[kind="header"] {
  display: none !important;
  color: transparent !important;
  font-size: 0px !important;
  visibility: hidden !important;
}
div[data-testid="collapsedControl"] { display: none !important; }

/* Make header light (avoid black flash) */
header[data-testid="stHeader"] {
  background: rgba(248, 249, 255, 0.85) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
header[data-testid="stHeader"] * {
  color: #0b1c30 !important;
}

/* App background */
.stApp {
  background: #f8f9ff; /* Corporate Precision Background */
}

/* Sidebar base */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #002045 0%, #1a365d 100%);
  border-right: none;
  box-shadow: 2px 0 16px rgba(0,0,0,0.06);
}

section[data-testid="stSidebar"] * {
  color: #ffffff;
  font-family: "Inter", ui-sans-serif, system-ui, -apple-system, sans-serif;
}

/* Sidebar content spacing */
section[data-testid="stSidebar"] .stSidebarContent {
  padding-top: 10px;
}

.sidebar-brand {
  padding: 18px 14px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 14px;
}

.brand-name {
  font-size: 14px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.08em;
}

.brand-sub {
  margin-top: 4px;
  font-size: 11px;
  color: #adc7f7; /* Inverse Primary */
  font-weight: 600;
  letter-spacing: 0.02em;
}

.sidebar-section {
  padding: 10px 12px 6px;
  font-size: 10px;
  font-weight: 800;
  color: rgba(255,255,255,0.4);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] a[data-testid="stPageLink"] {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 10px 14px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.75) !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  display: block;
  margin-bottom: 6px;
}

section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
  background: rgba(255,255,255,0.06);
  color: #ffffff !important;
  border-color: rgba(255,255,255,0.08);
  transform: translateX(2px);
}

/* "Primary" nav button (active) */
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"] {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.15);
  border-left: 3px solid #68abff; /* Secondary Container Accent */
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Sidebar Footer */
.sidebar-footer {
  margin-top: 24px;
  padding: 14px;
  border-top: 1px solid rgba(255,255,255,0.08);
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  text-align: center;
}

/* Badges */
.nav-badge-row {
  margin-top: -34px;
  margin-bottom: 14px;
  padding-right: 12px;
  display: flex;
  justify-content: flex-end;
  pointer-events: none;
}

.nav-badge {
  background: #0060ac;
  color: white;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Topbar Premium */
.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  background: #ffffff;
  border: 1px solid rgba(11,28,48,0.06);
  box-shadow: 0 4px 16px rgba(0,0,0,0.02);
  border-radius: 8px;
  margin: 18px 0 24px;
}

.topbar-breadcrumb {
  font-size: 13px;
  color: #74777f;
  font-weight: 500;
}

.topbar-breadcrumb span {
  color: #002045;
  font-weight: 800;
}

.topbar-spacer { flex: 1; }

.topbar-title {
  font-size: 15px;
  font-weight: 700;
  color: #0b1c30;
}

/* Generic Cards */
.card {
  background: #ffffff;
  border: 1px solid rgba(11,28,48,0.06);
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

/* Stat Grid */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-label {
  font-size: 11px;
  color: #74777f;
  font-weight: 700;
  letter-spacing: 0.10em;
  text-transform: uppercase;
}

.stat-value {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 800;
  color: #002045;
  font-family: "Inter", monospace, ui-sans-serif, system-ui;
}

/* Module Grid */
.section-title {
  font-size: 13px;
  font-weight: 800;
  color: #43474e;
  letter-spacing: 0.10em;
  margin: 10px 0 14px;
  text-transform: uppercase;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.module-card {
  background: #ffffff;
  border: 1px solid rgba(11,28,48,0.08);
  border-radius: 8px;
  padding: 22px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  overflow: hidden;
}

.module-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #002045, #0060ac);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.05);
  border-color: rgba(11,28,48,0.12);
}

.module-card:hover::before {
  opacity: 1;
}

.module-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #e5eeff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  font-size: 22px;
  color: #002045;
  font-weight: 700;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.04);
}

.module-title {
  font-size: 16px;
  font-weight: 800;
  color: #0b1c30;
  margin-bottom: 6px;
}

.module-desc {
  font-size: 13px;
  color: #43474e;
  line-height: 1.6;
  margin-bottom: 12px;
}

/* File uploader & UI Enhancements */
div[data-testid="stFileUploader"] {
  background: #ffffff;
  border: 1px dashed rgba(11,28,48,0.2) !important;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

div[data-testid="stFileUploader"]:hover {
  border-color: #0060ac !important;
  background: #f8f9ff;
}

/* Buttons */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
  background: linear-gradient(180deg, #0060ac 0%, #004b87 100%) !important;
  border: 1px solid #004b87 !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 10px rgba(0, 96, 172, 0.2) !important;
  transition: all 0.2s;
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
  background: linear-gradient(180deg, #006ebd 0%, #005494 100%) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0, 96, 172, 0.3) !important;
}

/* Reponsividade Elevada */
@media (max-width: 1024px) {
  .stat-grid { grid-template-columns: 1fr; gap: 12px; }
}

@media (max-width: 768px) {
  .topbar { flex-direction: column; height: auto; padding: 14px; align-items: flex-start; gap: 8px; }
  .topbar-spacer { display: none; }
  .module-grid { grid-template-columns: 1fr; }
  .nav-badge-row { display: none; }
}
"""
