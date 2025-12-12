import json
from dash import Dash, html, dcc, Output, Input, State
import dash

app = Dash(__name__)

sample_text = """Lemon Herb Roasted Chicken

Start by marinating the chicken thighs in a mixture of lemon juice,
minced garlic, fresh rosemary, thyme, and olive oil.
After an hour, place the chicken on a baking tray with sliced onions
and baby potatoes, then roast until the skin becomes crisp and golden.
"""

app.layout = html.Div(
    [
        html.H2("Interactive Text Annotator"),
        html.P(
            "Select some text below, enter a label, then click "
            "'Save selection' to store [start, end, label, text]. "
            "When you're done, click 'Finalize & download JSON'."
        ),

        # The text we are annotating
        html.Pre(
            id="text-block",
            children=sample_text,
            style={
                "whiteSpace": "pre-wrap",
                "border": "1px solid #ccc",
                "padding": "10px",
                "cursor": "text",
            },
        ),

        html.Br(),

        # Label input
        html.Div(
            [
                html.Label("Label for selected text:"),
                dcc.Input(
                    id="label-input",
                    type="text",
                    placeholder="e.g. INGREDIENT, PERSON, CITY",
                    style={"marginLeft": "10px", "width": "250px"},
                ),
            ]
        ),

        html.Br(),

        # Buttons
        html.Button("Save selection", id="save-selection", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Finalize & download JSON", id="finalize", n_clicks=0),

        html.Hr(),
        html.H4("Current annotations"),

        # Stores
        dcc.Store(id="selection-store"),          # latest raw selection from JS
        dcc.Store(id="selections-dict", data={'annotations':[]}), # accumulated selections in Python

        # Download component
        dcc.Download(id="download-json"),

        html.Pre(
            id="log",
            style={"backgroundColor": "#f9f9f9", "padding": "10px"},
        ),
    ]
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }

        var container = document.getElementById('text-block');
        if (!container) {
            return window.dash_clientside.no_update;
        }

        var selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            return window.dash_clientside.no_update;
        }

        var range = selection.getRangeAt(0);

        // Ensure the selection is inside our text block
        if (!container.contains(range.commonAncestorContainer)) {
            return window.dash_clientside.no_update;
        }

        // NOTE: This assumes selection is within a single text node of the <pre>
        var start = range.startOffset;
        var end = range.endOffset;
        var text = selection.toString();

        if (!text) {
            return window.dash_clientside.no_update;
        }

        return {
            "start": start,
            "end": end,
            "text": text
        };
    }
    """,
    Output("selection-store", "data"),
    Input("save-selection", "n_clicks"),
)

# ---------- Python callback: add [start, end, label, text] to dictionary ----------

@app.callback(
    Output("selections-dict", "data"),
    Output("log", "children"),
    Input("selection-store", "data"),
    State("selections-dict", "data"),
    State("label-input", "value"),
    prevent_initial_call=True,
)
def update_dict(latest_selection, selections_dict, label):
    if latest_selection is None:
        raise dash.exceptions.PreventUpdate

    text = (latest_selection.get("text") or "").strip()
    if not text:
        raise dash.exceptions.PreventUpdate

    start = int(latest_selection.get("start", 0))
    end = int(latest_selection.get("end", 0))
    label = label or ""  # allow empty label if user didn't type anything

    # Store as [start_index, end_index, label, selected_text]
    selections_dict['annotations'].append([start, end, label, text])

    pretty = json.dumps(selections_dict, indent=2, ensure_ascii=False)
    return selections_dict, pretty


# ---------- Download callback: finalize & download JSON ----------

@app.callback(
    Output("download-json", "data"),
    Input("finalize", "n_clicks"),
    State("selections-dict", "data"),
    prevent_initial_call=True,
)
def download_annotations(n_clicks, selections_dict):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # Fallback to empty dict if somehow None
    selections_dict = selections_dict or {'annotations':[]}

    # Return file for download
    return dcc.send_string(
        json.dumps(selections_dict, indent=2, ensure_ascii=False),
        "annotations.json"
    )


if __name__ == "__main__":
    app.run(debug=True)
