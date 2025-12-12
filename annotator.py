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
            "Edit or paste any text below, enter a label and select part of text in the text area, "
            ", then click 'Save selection' to store "
            "[start, end, label]. When you're done, click "
            "'Finalize & download JSON'."
        ),

        # Editable text widget
        dcc.Textarea(
            id="text-input",
            value=sample_text,
            style={
                "width": "100%",
                "height": "200px",
                "border": "1px solid #ccc",
                "padding": "10px",
                "fontFamily": "monospace",
                "whiteSpace": "pre",
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
        html.Button(
            "Save selection",
            id="save-selection",
            n_clicks=0,
            style={"marginRight": "10px"},
        ),
        html.Button("Finalize & download JSON", id="finalize", n_clicks=0),

        html.Hr(),
        html.H4("Current selections dictionary"),

        # Stores
        dcc.Store(id="selection-store"),          # latest selection from JS
        dcc.Store(id="selections-dict", data={'annotations':[]}), # accumulated selections

        # Download component
        dcc.Download(id="download-json"),

        html.Pre(
            id="log",
            style={"backgroundColor": "#f9f9f9", "padding": "10px"},
        ),
    ]
)

# ---------- Clientside callback: get selection & indices from the textarea ----------

app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }

        var textarea = document.getElementById('text-input');
        if (!textarea) {
            return window.dash_clientside.no_update;
        }

        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        if (start === end) {
            // nothing selected
            return window.dash_clientside.no_update;
        }

        var fullText = textarea.value || "";
        var text = fullText.slice(start, end);

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

# ---------- Single Python callback: update dict OR download & reset ----------

@app.callback(
    Output("selections-dict", "data"),
    Output("log", "children"),
    Output("download-json", "data"),
    Input("selection-store", "data"),
    Input("finalize", "n_clicks"),
    State("selections-dict", "data"),
    State("label-input", "value"),
    prevent_initial_call=True,
)
def handle_actions(latest_selection, finalize_clicks, selections_dict, label):
    ctx = dash.callback_context

    # We'll always start from the existing dict (or empty)
    selections_dict = selections_dict or {'annotations':[]}
    download_data = None  # default: no download

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Case 1: new selection came in from selection-store
    if prop_id == "selection-store":
        if latest_selection is None:
            raise dash.exceptions.PreventUpdate

        text = (latest_selection.get("text") or "").strip()
        if not text:
            raise dash.exceptions.PreventUpdate

        start = int(latest_selection.get("start", 0))
        end = int(latest_selection.get("end", 0))
        label = label or ""  # allow empty label

        # Store as [start_index, end_index, label]
        selections_dict['annotations'].append([start, end, label])

    # Case 2: finalize button clicked → download & reset
    elif prop_id == "finalize":
        # Prepare download of current selections
        json_str = json.dumps(selections_dict, indent=2, ensure_ascii=False)
        download_data = dcc.send_string(json_str, "annotations.json")

        # Reset selections after download
        selections_dict = {'annotations': []}

    # Update log view
    pretty = json.dumps(selections_dict, indent=2, ensure_ascii=False) if selections_dict else "{}"

    return selections_dict, pretty, download_data


if __name__ == "__main__":
    app.run(debug=True)
