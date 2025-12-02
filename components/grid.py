# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
from components.grid_options import configure_column_editors

COLUMN_BID = "Bid"

# ==============================================================================
# JAVASCRIPT DEFINITIONS (Consolidated for reliability)
# ==============================================================================

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

# FIXED: Updated to handle both 'URL' and 'url' keys safely
JS_ACTIONS_RENDERER = JsCode("""
class ActionsRenderer {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.style.display = 'flex';
        this.eGui.style.justifyContent = 'center';
        this.eGui.style.alignItems = 'center';
        this.eGui.style.height = '100%';
        
        // Look for URL in various common keys
        const url = params.data.URL || params.data.url || params.data.productUrl;

        if (url) {
            const link = document.createElement('a');
            link.href = url;
            link.target = "_blank";
            link.innerText = "🔗"; 
            link.style.textDecoration = "none";
            link.style.fontSize = "16px";
            link.title = "Open Link";
            this.eGui.appendChild(link);
        }
    }
    getGui() { return this.eGui; }
}
""")

JS_ROW_STYLE = JsCode("""
function(params) {
    if (params.data.is_hidden === 1) return {'color': '#9e9e9e', 'backgroundColor': '#f5f5f5', 'text-decoration': 'line-through', 'font-style': 'italic'};
    if (params.data.Risk === 'HIGH RISK') return {'backgroundColor': '#ffcdd2', 'color': 'black'}; 
    if (params.data.Risk === 'MEDIUM RISK') return {'backgroundColor': '#ffe0b2', 'color': 'black'}; 
    if (params.data.Risk === 'NO BIDS') return {'backgroundColor': '#e3f2fd', 'color': 'black'}; 
    return {};
}
""")

JS_RISK_CELL_STYLE = JsCode("""
function(params) {
    if (params.value === 'HIGH RISK') return {'color': '#d32f2f', 'fontWeight': 'bold'};
    if (params.value === 'MEDIUM RISK') return {'color': '#e65100', 'fontWeight': 'bold'};
    if (params.value === 'NO BIDS') return {'color': '#1565c0', 'fontWeight': 'bold'};
    return {};
}
""")

JS_PROFIT_STYLE = JsCode("""function(params) { if (params.value > 0) return {'color': '#2e7d32', 'fontWeight': 'bold'}; if (params.value < 0) return {'color': '#c62828', 'fontWeight': 'bold'}; return {}; }""")
JS_BID_PCT_STYLE = JsCode("""function(params) { const val = parseFloat(String(params.value).replace('%','')); if (val > 70) return {'color': '#c62828', 'fontWeight': 'bold'}; if (val > 50) return {'color': '#ef6c00', 'fontWeight': 'bold'}; return {}; }""")

JS_STYLE_BAD_YES = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'yes') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_NO = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'no') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")
JS_STYLE_BAD_COND = JsCode("""function(params) { if (String(params.value).toLowerCase().trim() === 'for parts only') { return {'fontWeight': 'bold', 'color': '#b71c1c'}; } return {}; }""")

JS_NATURAL_SORT = JsCode(r"""function(a,b){return a.localeCompare(b, undefined, {numeric: true, sensitivity: 'base'});}""")
JS_CURRENCY_SORT = JsCode(r"""function(a,b){return (parseFloat(String(a).replace(/[$,]/g,''))||0) - (parseFloat(String(b).replace(/[$,]/g,''))||0);}""")

def get_persistence_js(grid_id):
    return JsCode(f"""
    function(params) {{
        const storageKey = 'auctapp_state_' + '{grid_id}';
        const saved = localStorage.getItem(storageKey);
        if (saved) {{
            const s = JSON.parse(saved);
            if (s.colState) params.api.setColumnState(s.colState);
            if (s.filterState) params.api.setFilterModel(s.filterState);
        }}
        function save() {{
            const s = {{ colState: params.api.getColumnState(), filterState: params.api.getFilterModel() }};
            localStorage.setItem(storageKey, JSON.stringify(s));
        }}
        ['columnVisible','columnPinned','columnResized','columnMoved','filterChanged'].forEach(e => params.api.addEventListener(e, save));
    }}
    """)

# ==============================================================================
# CONFIGURATION HELPERS
# ==============================================================================
COLUMN_BID = "Bid"

def _configure_columns(gb: GridOptionsBuilder, df: pd.DataFrame):
    columns = df.columns
    
    # Hidden Columns
    hidden = ["id", "current_bid", "is_hidden", "product_id", "auction_id", "sold_price", "suggested_msrp", "url", "master_msrp", "master_target_price", "profit_val", "MSRP Status", "scraped_category"]
    for col in hidden:
        if col in columns: gb.configure_column(col, hide=True)

    # 1. Select
    if "Select" in columns:
        gb.configure_column("Select", checkboxSelection=True, headerCheckboxSelection=True, width=50, pinned="left", headerName="Select", suppressMenu=True, valueFormatter=JS_EMPTY_TEXT)
    
    # 2. Actions (FIXED)
    if "Actions" in columns:
        gb.configure_column("Actions", cellRenderer=JS_ACTIONS_RENDERER, width=50, pinned="left", headerName="", suppressMenu=True)

    # 3. Risk
    if "Risk" in columns: gb.configure_column("Risk", width=130, pinned="left", cellStyle=JS_RISK_CELL_STYLE)

    # 4. Watch
    if "Watch" in columns:
        gb.configure_column("Watch", editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="⭐")

    # Metrics
    if "Est. Profit" in columns: gb.configure_column("Est. Profit", width=100, cellStyle=JS_PROFIT_STYLE, comparator=JS_CURRENCY_SORT)
    if "Bid %" in columns: gb.configure_column("Bid %", width=80, cellStyle=JS_BID_PERCENT_STYLE)
    if "MSRP" in columns: gb.configure_column("MSRP", width=90)

    # Sorters & Widths
    text_cols = ["Lot", "Title", "Brand", "Model", "UPC", "ASIN", "Category", "Scraped MSRP"]
    for col in text_cols:
        if col in columns: gb.configure_column(col, comparator=JS_NATURAL_SORT)
    if COLUMN_BID in columns: gb.configure_column(COLUMN_BID, width=100, comparator=JS_CURRENCY_SORT)

    # Styles
    if "Functional" in columns: gb.configure_column("Functional", cellStyle=JS_STYLE_BAD_NO)
    if "Condition" in columns: gb.configure_column("Condition", cellStyle=JS_STYLE_BAD_COND)
    for col in ["Damaged", "Missing Parts"]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_BAD_YES)

    configure_column_editors(gb)

def render_grid(df: pd.DataFrame, height: int = 650, allow_selection: bool = True, grid_key: str = "default"):
    if df is None or df.empty: return {"selected": [], "data": df}

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(getRowStyle=JS_ROW_STYLE)
    gb.configure_grid_options(enableRangeSelection=True) 
    gb.configure_grid_options(rowSelection='multiple')
    gb.configure_grid_options(onGridReady=get_persistence_js(grid_key))
    
    _configure_columns(gb, df)

    if allow_selection:
        gb.configure_selection(selection_mode="multiple", use_checkbox=False, header_checkbox=False, suppressRowClickSelection=True)

    grid_options = gb.build()

    return AgGrid(
        df, gridOptions=grid_options, height=height, 
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.MODEL_CHANGED, 
        allow_unsafe_jscode=True, theme="streamlit",
        key=f"ag_grid_{grid_key}"
    )