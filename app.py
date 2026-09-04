from flask import Flask, render_template, request
from utils import preprocess_and_save
import pandas as pd
from groq import Groq

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    df = None
    df_html = ""
    df_preview_html = ""
    result_html = ""
    code_generated = ""

    if request.method == "POST":
        file = request.files.get("file")
        query = request.form.get("query")
        groq_key = request.form.get("api_key")

        if not groq_key:
            message = "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"
        elif file:
            df, cols, df_html, err = preprocess_and_save(file)
            if err:
                message = err
            else:
                # Show first 5 rows preview
                df_preview_html = df.head().to_html(classes="table-auto w-full") if df is not None else ""

                if query:
                    try:
                        columns = ", ".join(df.columns)

                        prompt = f"""
You are an expert Python data analyst.

You are given a pandas DataFrame named `df`.

The EXACT columns available in the DataFrame are:

{columns}

User question:
{query}

IMPORTANT RULES:

1. Use ONLY the columns listed above.
2. Use the EXACT column names shown above.
3. NEVER invent a column name.
4. Do not create columns such as "has_diabetes", "diabetes", or "is_diabetic"
   unless they already exist in the provided column list.
5. Use the existing DataFrame named `df`.
6. Do not load another dataset.
7. Use pandas.
8. Store the final answer in a variable called `result`.
9. Return ONLY executable Python code.
10. Do not include explanations.
11. Do not use markdown code fences.

For example, if the user asks about diabetes and the dataset contains
an `Outcome` column, use `df["Outcome"]`.
"""

                        client = Groq(api_key=groq_key)
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="openai/gpt-oss-120b"
                        )

                        code_generated = chat_completion.choices[0].message.content.strip("`python").strip("`")

                        local_vars = {"df": df}
                        exec(code_generated, {}, local_vars)

                        result = local_vars.get("result", "No result generated.")
                        if isinstance(result, pd.DataFrame):
                            result_html = result.to_html(classes="table-auto w-full")
                        else:
                            result_html = str(result)

                    except Exception as e:
                        message = f"Error running Groq code: {e}"

        else:
            message = "Please upload a file."

    return render_template(
        "index.html",
        message=message,
        df_html=df_html,
        df_preview_html=df_preview_html,
        code_generated=code_generated,
        result_html=result_html,
    )

if __name__ == "__main__":
    app.run(debug=True)
