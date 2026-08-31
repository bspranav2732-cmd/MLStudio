import sys
import os
import streamlit as st

def _is_windows_dark_mode() -> bool:
    """Check if Windows is currently in Dark Mode."""
    try:
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False

def get_current_mode(selected_mode: str) -> str:
    """Resolves 'Follow System' to 'Light' or 'Dark'."""
    if selected_mode in ("Follow System", "System"):
        if sys.platform == "win32":
            return "Dark" if _is_windows_dark_mode() else "Light"
        return "Light"
    return selected_mode

def get_palette(mode: str) -> dict:
    resolved_mode = get_current_mode(mode)
    
    if resolved_mode == "Dark":
        return {
            "bg": "#1e1e20",
            "surface": "#25262b",
            "sidebar_bg": "#25262b",
            "accent": "#ff4b4b",
            "text_primary": "#f2f3f5",
            "text_muted": "#a0a3a8",
            "border": "#3f4045",
            
            "success_bg": "#1e3b26",
            "success_text": "#81c995",
            "success_border": "#2d5a3a",
            
            "warn_bg": "#4a3c18",
            "warn_text": "#fde293",
            "warn_border": "#6e5922",
            
            "err_bg": "#4a1c1a",
            "err_text": "#f28b82",
            "err_border": "#6e2926",
            
            "info_bg": "#18325a",
            "info_text": "#8ab4f8",
            "info_border": "#224a87"
        }
    else:
        return {
            "bg": "#ffffff",
            "surface": "#ffffff",
            "sidebar_bg": "#f8f9fa",
            "accent": "#0056b3",
            "text_primary": "#212529",
            "text_muted": "#6c757d",
            "border": "#dee2e6",
            
            "success_bg": "#e6f4ea",
            "success_text": "#137333",
            "success_border": "#ceead6",
            
            "warn_bg": "#fef7e0",
            "warn_text": "#b06000",
            "warn_border": "#feefc3",
            
            "err_bg": "#fce8e6",
            "err_text": "#c5221f",
            "err_border": "#fad2cf",
            
            "info_bg": "#e8f0fe",
            "info_text": "#1967d2",
            "info_border": "#d2e3fc"
        }

def style_file_uploader(p: dict) -> str:
    return f"""
    [data-testid="stFileUploader"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }}
    [data-testid="stFileUploader"] section {{
        background-color: transparent !important;
        color: {p["text_muted"]} !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: transparent !important;
    }}
    """

def style_dataframe(p: dict) -> str:
    return f"""
    [data-testid="stDataFrame"] {{
        border: 1px solid {p["border"]} !important;
        border-radius: 8px !important;
        background-color: {p["surface"]} !important;
    }}
    [data-testid="stTable"] {{
        background-color: {p["surface"]} !important;
        color: {p["text_primary"]} !important;
    }}
    """

def style_buttons(p: dict) -> str:
    return f"""
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stButton"] button {{
        border: 1px solid {p["border"]} !important;
        border-radius: 6px !important;
        background-color: {p["surface"]} !important;
        color: {p["text_primary"]} !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stButton"] button:hover {{
        border-color: {p["accent"]} !important;
        color: {p["accent"]} !important;
        background-color: {p["bg"]} !important;
    }}
    [data-testid="stBaseButton-primary"] {{
        background-color: {p["accent"]} !important;
        color: #ffffff !important;
        border: none !important;
    }}
    [data-testid="stBaseButton-primary"]:hover {{
        background-color: {p["text_primary"]} !important;
        color: {p["bg"]} !important;
    }}
    """

def style_metrics(p: dict) -> str:
    return f"""
    [data-testid="stMetric"] {{
        background-color: {p["sidebar_bg"]} !important;
        border: 1px solid {p["border"]} !important;
        padding: 15px !important;
        border-radius: 8px !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {p["text_muted"]} !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {p["text_primary"]} !important;
    }}
    """

def style_tabs(p: dict) -> str:
    return f"""
    [data-testid="stTabBar"] {{
        border-bottom: 1px solid {p["border"]} !important;
        background-color: {p["sidebar_bg"]} !important;
    }}
    [data-testid="stTab"] {{
        color: {p["text_muted"]} !important;
        background-color: transparent !important;
    }}
    [data-testid="stTab"][aria-selected="true"] {{
        color: {p["accent"]} !important;
        background-color: {p["bg"]} !important;
        border: 1px solid {p["border"]} !important;
        border-bottom: 1px solid {p["bg"]} !important;
    }}
    """

def style_forms(p: dict) -> str:
    return f"""
    [data-testid="stForm"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }}
    """

def style_selectboxes(p: dict) -> str:
    return f"""
    [data-testid="stSelectbox"] div[data-baseweb="select"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
        color: {p["text_primary"]} !important;
    }}
    [data-testid="stSelectbox"] div[data-baseweb="popover"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
    }}
    [data-testid="stSelectbox"] li {{
        color: {p["text_primary"]} !important;
    }}
    [data-testid="stSelectbox"] li:hover {{
        background-color: {p["sidebar_bg"]} !important;
    }}
    """

def style_expanders(p: dict) -> str:
    return f"""
    [data-testid="stExpander"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stExpander"] summary {{
        color: {p["text_primary"]} !important;
        background-color: {p["sidebar_bg"]} !important;
    }}
    """

def style_success_boxes(p: dict) -> str:
    return f"""
    [data-testid="stAlert"]:has(svg[data-testid="stIconSuccess"]),
    div[data-baseweb="notification"][style*="success"] {{
        background-color: {p["success_bg"]} !important;
        color: {p["success_text"]} !important;
        border: 1px solid {p["success_border"]} !important;
    }}
    """

def style_warning_boxes(p: dict) -> str:
    return f"""
    [data-testid="stAlert"]:has(svg[data-testid="stIconWarning"]),
    div[data-baseweb="notification"][style*="warning"] {{
        background-color: {p["warn_bg"]} !important;
        color: {p["warn_text"]} !important;
        border: 1px solid {p["warn_border"]} !important;
    }}
    """

def style_error_boxes(p: dict) -> str:
    return f"""
    [data-testid="stAlert"]:has(svg[data-testid="stIconError"]),
    div[data-baseweb="notification"][style*="negative"] {{
        background-color: {p["err_bg"]} !important;
        color: {p["err_text"]} !important;
        border: 1px solid {p["err_border"]} !important;
    }}
    """

def style_info_boxes(p: dict) -> str:
    return f"""
    [data-testid="stAlert"]:has(svg[data-testid="stIconInfo"]),
    div[data-baseweb="notification"][style*="info"] {{
        background-color: {p["info_bg"]} !important;
        color: {p["info_text"]} !important;
        border: 1px solid {p["info_border"]} !important;
    }}
    """

def style_markdown(p: dict) -> str:
    return f"""
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
        color: {p["text_primary"]} !important;
    }}
    """

def style_sidebar(p: dict) -> str:
    return f"""
    [data-testid="stSidebar"] {{
        background-color: {p["sidebar_bg"]} !important;
        border-right: 1px solid {p["border"]} !important;
    }}
    """

def style_inputs(p: dict) -> str:
    return f"""
    /* Text, Number, and Multiselect Inputs */
    [data-testid="stTextInput"] input, 
    [data-testid="stNumberInput"] input,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] {{
        background-color: {p["surface"]} !important;
        border: 1px solid {p["border"]} !important;
        color: {p["text_primary"]} !important;
    }}
    
    /* Multiselect tags */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
        background-color: {p["sidebar_bg"]} !important;
        color: {p["text_primary"]} !important;
        border: 1px solid {p["border"]} !important;
    }}
    
    /* Checkbox & Radio Labels */
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {{
        color: {p["text_primary"]} !important;
    }}
    
    /* Slider Text */
    [data-testid="stSlider"] div,
    [data-testid="stSlider"] span {{
        color: {p["text_primary"]} !important;
    }}
    """

def style_root_variables(p: dict) -> str:
    return f"""
    :root {{
        --primary-color: {p["accent"]} !important;
        --background-color: {p["bg"]} !important;
        --secondary-background-color: {p["sidebar_bg"]} !important;
        --text-color: {p["text_primary"]} !important;
        --font: "sans-serif" !important;
    }}
    """

def get_plot_theme(mode: str) -> dict:
    p = get_palette(mode)
    resolved_mode = get_current_mode(mode)
    return {
        "style": "darkgrid" if resolved_mode == "Dark" else "whitegrid",
        "rc": {
            "font.family": "serif",
            "font.size": 12,
            "axes.labelsize": 14,
            "axes.titlesize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 10,
            "figure.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.3 if resolved_mode == "Dark" else 0.5,
            "grid.color": p["border"],
            "grid.linestyle": "-",
            "figure.facecolor": p["bg"],
            "axes.facecolor": p["surface"],
            "axes.edgecolor": p["border"],
            "text.color": p["text_primary"],
            "axes.labelcolor": p["text_primary"],
            "xtick.color": p["text_muted"],
            "ytick.color": p["text_muted"]
        }
    }

def inject_css() -> None:
    mode = st.session_state.get("appearance", "Light")
    p = get_palette(mode)
    
    is_frozen = getattr(sys, "frozen", False)
    is_debug = os.environ.get("SOLVOSYS_DEBUG") == "1"
    
    chrome_css = ""
    if is_frozen and not is_debug:
        chrome_css = """
        /* HIDE STREAMLIT CHROME IN PRODUCTION */
        [data-testid="stHeader"] { display: none !important; }
        #MainMenu { display: none !important; }
        .stDeployButton { display: none !important; }
        footer { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        """
        
    css = f"""
    <style>
    {chrome_css}
    
    {style_root_variables(p)}
    
    /* Root Application Backgrounds */
    html, body, .stApp, .main, .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {{
        background-color: {p["bg"]} !important;
        color: {p["text_primary"]} !important;
    }}

    /* Make the header transparent (useful for Debug mode) */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    
    {style_sidebar(p)}
    {style_file_uploader(p)}
    {style_dataframe(p)}
    {style_buttons(p)}
    {style_metrics(p)}
    {style_tabs(p)}
    {style_forms(p)}
    {style_selectboxes(p)}
    {style_inputs(p)}
    {style_expanders(p)}
    {style_success_boxes(p)}
    {style_warning_boxes(p)}
    {style_error_boxes(p)}
    {style_info_boxes(p)}
    {style_markdown(p)}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
