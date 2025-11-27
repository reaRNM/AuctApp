from st_aggrid import JsCode

JS_EMPTY_TEXT = JsCode("""function(params) { return ""; }""")

JS_CHECKBOX_RENDERER = JsCode("""
class CheckboxRenderer {
    init(params) {
        this.eGui = document.createElement('input');
        this.eGui.type = 'checkbox';
        this.eGui.checked = params.value;
        this.eGui.onclick = function (evt) {
            params.setValue(this.checked);
        };
        this.eGui.style.display = 'block';
        this.eGui.style.margin = 'auto';
        this.eGui.style.cursor = 'pointer';
    }
    getGui() { return this.eGui; }
}
""")

JS_ROW_STYLE = JsCode("""
function(params) {
    if (params.data.is_hidden === 1) {
        return {'color': '#9e9e9e', 'backgroundColor': '#f5f5f5', 'text-decoration': 'line-through', 'font-style': 'italic'};
    }
    if (params.data.Risk === 'HIGH RISK') return {'backgroundColor': '#ffcdd2', 'color': 'black'}; 
    if (params.data.Risk === 'MEDIUM RISK') return {'backgroundColor': '#ffe0b2', 'color': 'black'}; 
    if (params.data.Risk === 'NO BIDS') return {'backgroundColor': '#e3f2fd', 'color': 'black'}; 
    return {};
}
""")

# === NEW: ACTIONS RENDERER (Open Link Button) ===
JS_ACTIONS_RENDERER = JsCode("""
class ActionsRenderer {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.style.display = 'flex';
        this.eGui.style.justifyContent = 'center';
        this.eGui.style.alignItems = 'center';
        this.eGui.style.height = '100%';

        // Link Button (🔗)
        if (params.data.url) {
            const linkBtn = document.createElement('a');
            linkBtn.href = params.data.url;
            linkBtn.target = "_blank";
            linkBtn.innerText = "🔗";
            linkBtn.style.textDecoration = "none";
            linkBtn.style.fontSize = "16px";
            linkBtn.style.cursor = "pointer";
            linkBtn.title = "Open Auction Page";
            this.eGui.appendChild(linkBtn);
        }
    }
    getGui() { return this.eGui; }
}
""")

# === NEW: PROFIT STYLING ===
JS_PROFIT_STYLE = JsCode("""
function(params) {
    if (params.value > 0) return {'color': '#2e7d32', 'fontWeight': 'bold'}; // Green
    if (params.value < 0) return {'color': '#c62828', 'fontWeight': 'bold'}; // Red
    return {};
}
""")

# === NEW: BID % STYLING (Warn if > 50% of MSRP) ===
JS_BID_PERCENT_STYLE = JsCode("""
function(params) {
    // Remove % and parse
    const val = parseFloat(String(params.value).replace('%',''));
    if (val > 70) return {'color': '#c62828', 'fontWeight': 'bold'}; // High Risk
    if (val > 50) return {'color': '#ef6c00', 'fontWeight': 'bold'}; // Warning
    if (val > 0)  return {'color': '#2e7d32', 'fontWeight': 'bold'}; // Good deal
    return {};
}
""")

JS_STYLE_BAD_YES = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'yes') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_NO = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'no') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_COND = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'for parts only') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")

JS_NATURAL_SORT = JsCode(r"""function(a,b){return a.localeCompare(b, undefined, {numeric: true, sensitivity: 'base'});}""")
JS_CURRENCY_SORT = JsCode(r"""function(a,b){return (parseFloat(String(a).replace(/[$,]/g,''))||0) - (parseFloat(String(b).replace(/[$,]/g,''))||0);}""")