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
JS_MSRP_STYLE = JsCode("""function(params) { if (params.value > 0) return {fontWeight: 'bold', color: '#2E86C1'}; return {}; }""")


# === UNIFIED RISK STYLES (High + Medium) ===

# CONDITION: High = Parts Only (Red) | Medium = Used/Bad (Orange)
JS_STYLE_CONDITION = JsCode("""
function(params) { 
    const val = String(params.value).toLowerCase().trim();
    if (val === 'for parts only') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; }
    if (val === 'used' || val === 'bad') { return {'fontWeight': 'bold', 'color': '#ef6c00'}; }
    return {}; 
}
""")

# FUNCTIONAL: High = No (Red) | Medium = Unable/Unknown (Orange)
JS_STYLE_FUNCTIONAL = JsCode("""
function(params) { 
    const val = String(params.value).toLowerCase().trim();
    if (val === 'no') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; }
    if (val.includes('unable') || val.includes('unknown')) { return {'fontWeight': 'bold', 'color': '#ef6c00'}; }
    return {}; 
}
""")

# BINARY (Missing/Damaged): High = Yes (Red) | Medium = Unknown (Orange)
JS_STYLE_BINARY_FLAG = JsCode("""
function(params) { 
    const val = String(params.value).toLowerCase().trim();
    if (val === 'yes' || val === 'true') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; }
    if (val.includes('unknown')) { return {'fontWeight': 'bold', 'color': '#ef6c00'}; }
    return {}; 
}
""")

# PACKAGING: Medium = No/Damaged (Orange)
JS_STYLE_PACKAGING = JsCode("""
function(params) { 
    const val = String(params.value).toLowerCase().trim();
    if (val.includes('no') || val.includes('open box - tested') || val.includes('damaged') || val.includes('not in original')) { return {'fontWeight': 'bold', 'color': '#ef6c00'}; } 
    return {}; 
}
""")

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