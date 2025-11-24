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

# 2. ROW STYLING (Whole Row)
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

# 3. CELL STYLING (Specific Flags)
JS_STYLE_BAD_YES = JsCode("""
function(params) {
    if (String(params.value).toLowerCase().trim() === 'yes') {
        return {'fontWeight': 'bold', 'color': '#b71c1c'}; 
    }
    return {};
}
""")

JS_STYLE_BAD_NO = JsCode("""
function(params) {
    if (String(params.value).toLowerCase().trim() === 'no') {
        return {'fontWeight': 'bold', 'color': '#b71c1c'}; 
    }
    return {};
}
""")

JS_STYLE_BAD_COND = JsCode("""
function(params) {
    if (String(params.value).toLowerCase().trim() === 'for parts only') {
        return {'fontWeight': 'bold', 'color': '#b71c1c'}; 
    }
    return {};
}
""")

# 4. SORTERS
JS_NATURAL_SORT = JsCode(r"""function(a,b){return a.localeCompare(b, undefined, {numeric: true, sensitivity: 'base'});}""")
JS_CURRENCY_SORT = JsCode(r"""function(a,b){return (parseFloat(String(a).replace(/[$,]/g,''))||0) - (parseFloat(String(b).replace(/[$,]/g,''))||0);}""")