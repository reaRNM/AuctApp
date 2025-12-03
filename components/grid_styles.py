# components/grid_styles.py
from st_aggrid import JsCode

# 1. RENDERERS
JS_EMPTY_TEXT = JsCode("""function(params) { return ""; }""")

JS_CHECKBOX_RENDERER = JsCode("""
class CheckboxRenderer {
    init(params) {
        this.eGui = document.createElement('input');
        this.eGui.type = 'checkbox';
        this.eGui.checked = params.value;
        this.eGui.onclick = function (evt) { params.setValue(this.checked); };
        this.eGui.style.display = 'block';
        this.eGui.style.margin = 'auto';
        this.eGui.style.cursor = 'pointer';
    }
    getGui() { return this.eGui; }
}
""")

# This was the missing one that caused issues before
JS_ACTIONS_RENDERER = JsCode("""
class ActionsRenderer {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.style.display = 'flex';
        this.eGui.style.justifyContent = 'center';
        this.eGui.style.alignItems = 'center';
        this.eGui.style.height = '100%';

        const href = params.value || (params.data && (params.data.url || params.data.URL));
        if (href) {
            const linkBtn = document.createElement('a');
            linkBtn.href = href;
            linkBtn.target = "_blank";
            linkBtn.rel = "noopener noreferrer";
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

# 2. ROW STYLING
JS_ROW_STYLE = JsCode("""
function(params) {
    if (params.data.is_hidden === 1) return {'color': '#9e9e9e', 'backgroundColor': '#f5f5f5', 'text-decoration': 'line-through', 'font-style': 'italic'};
    if (params.data.Risk === 'HIGH RISK') return {'backgroundColor': '#ffcdd2', 'color': 'black'}; 
    if (params.data.Risk === 'MEDIUM RISK') return {'backgroundColor': '#ffe0b2', 'color': 'black'}; 
    if (params.data.Risk === 'NO BIDS') return {'backgroundColor': '#e3f2fd', 'color': 'black'}; 
    return {};
}
""")

# 3. CELL STYLING
JS_RISK_CELL_STYLE = JsCode("""
function(params) {
    if (params.value === 'HIGH RISK') return {'color': '#d32f2f', 'fontWeight': 'bold'};
    if (params.value === 'MEDIUM RISK') return {'color': '#e65100', 'fontWeight': 'bold'};
    if (params.value === 'NO BIDS') return {'color': '#1565c0', 'fontWeight': 'bold'};
    return {};
}
""")

JS_PROFIT_STYLE = JsCode("""function(params) { if (params.value > 0) return {'color': '#2e7d32', 'fontWeight': 'bold'}; if (params.value < 0) return {'color': '#c62828', 'fontWeight': 'bold'}; return {}; }""")
JS_BID_PERCENT_STYLE = JsCode("""function(params) { const val = parseFloat(String(params.value).replace('%','')); if (val > 70) return {'color': '#c62828', 'fontWeight': 'bold'}; if (val > 50) return {'color': '#ef6c00', 'fontWeight': 'bold'}; return {}; }""")

JS_STYLE_BAD_YES = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'yes') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_NO = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'no') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_COND = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'for parts only') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")

# 4. SORTERS
JS_NATURAL_SORT = JsCode(r"""function(a,b){return a.localeCompare(b, undefined, {numeric: true, sensitivity: 'base'});}""")
JS_CURRENCY_SORT = JsCode(r"""function(a,b){return (parseFloat(String(a).replace(/[$,]/g,''))||0) - (parseFloat(String(b).replace(/[$,]/g,''))||0);}""")

# 5. PERSISTENCE
def get_persistence_js(grid_id):
    """Returns the JsCode needed to save/restore state for a specific grid ID."""
    return JsCode(f"""
    function(params) {{
        const gridId = '{grid_id}';
        const storageKey = 'auctapp_state_' + gridId;

        const savedState = localStorage.getItem(storageKey);
        if (savedState) {{
            const state = JSON.parse(savedState);
            if (state.colState) {{ params.api.setColumnState(state.colState); }}
            if (state.filterState) {{ params.api.setFilterModel(state.filterState); }}
        }}

        function saveState() {{
            const state = {{
                colState: params.api.getColumnState(),
                filterState: params.api.getFilterModel()
            }};
            localStorage.setItem(storageKey, JSON.stringify(state));
        }}

        params.api.addEventListener('columnVisible', saveState);
        params.api.addEventListener('columnPinned', saveState);
        params.api.addEventListener('columnResized', saveState);
        params.api.addEventListener('columnMoved', saveState);
        params.api.addEventListener('filterChanged', saveState);
    }}
    """)
