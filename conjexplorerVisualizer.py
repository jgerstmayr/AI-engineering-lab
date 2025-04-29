# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: conjexplorerVisualizer.py
#
# Details:  Visualizes and compares model evaluation scores across conjectures using interactive heatmaps and stacked bar plots.
#
# Authors:  Michael Pieber
# Date:     2025-04-15
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
# Requirements: 
# 
# pip install dash
# pip install plotly
# pip install openpyxl
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import re
import json
    
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
import dash
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from pathlib import Path
import re
import os
from time import time

# import templatesAndLists

base_folder = "logsAgent/logsFinal_r2_c8"

modelName2mbsID = {}
mbsID2modelName = {}
model_data_cache = {}
cntID = 1

# Define all available models (only those with results.json)
available_models = sorted([
    f.name for f in Path(base_folder).iterdir()
    if f.is_dir() and (f / "results.json").exists()
])

def get_model_paths(selected_model):
    """Given a selected model, return all important paths."""
    path_to_model = Path(base_folder) / selected_model
    relative_path = path_to_model / "results.json"
    output_dir = path_to_model / "output" / "figures"
    filepath_save_load = output_dir / "updated_data.json"

    # Ensure output folder exists
    os.makedirs(output_dir, exist_ok=True)

    return {
        "model_path": path_to_model,
        "results_json": relative_path,
        "output_dir": output_dir,
        "save_path": filepath_save_load
    }



cntID = 1
base_name_to_id = {}  # 👈 must be global and consistent
base_name_index = defaultdict(int)

# evalMethod2ID = {}
# ID2evalMethod = {}
# cntEvalMethod = 1

# def register_eval_method(method_name):
#     global cntEvalMethod, evalMethod2ID, ID2evalMethod
#     if method_name not in evalMethod2ID:
#         evalMethod2ID[method_name] = cntEvalMethod
#         ID2evalMethod[cntEvalMethod] = method_name
#         cntEvalMethod += 1

# pull in the “paper” dict
# (make sure templatesAndLists.dictOfEvaluationMethods is already defined there)
from templatesAndLists import dictOfEvaluationMethods

# our two globals stay — they’ll be
# completely rebuilt from dictOfEvaluationMethods
cntEvalMethod = 1
evalMethod2ID = {}
ID2evalMethod = {}

def register_eval_method(method_name):
    """
    Ensure method_name is in your paper dict,
    then re-assign every method its paper-dict ID
    in insertion order, and mirror that into our globals.
    """
    # 1) make sure it exists
    if method_name not in dictOfEvaluationMethods:
        dictOfEvaluationMethods[method_name] = {}

    # 2) re-number *all* entries, in dict order:
    cnt = 1
    for key in dictOfEvaluationMethods:
        dictOfEvaluationMethods[key]['ID'] = cnt
        cnt += 1

    # 3) mirror into our globals
    evalMethod2ID.clear()
    ID2evalMethod.clear()
    for key, info in dictOfEvaluationMethods.items():
        eid = info['ID']
        evalMethod2ID[key] = eid
        ID2evalMethod[eid] = key

    # 4) bump our next free counter so existing code that
    #    compares to cntEvalMethod still works (though you
    #    never actually use cntEvalMethod any more):
    global cntEvalMethod
    cntEvalMethod = cnt








def load_model_data(model_name):
    global modelName2mbsID, mbsID2modelName, cntID, base_name_to_id, base_name_index

    full_path = Path(base_folder) / model_name / "results.json"
    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    model_descriptions = data.get("allMbsModelsDict", {})

    for model_key in model_descriptions:
        if model_key in modelName2mbsID:
            continue  # Already assigned

        base_name = re.sub(r"\d+$", "", model_key)
        if base_name not in base_name_to_id:
            base_name_to_id[base_name] = cntID
            cntID += 1

        group_id = base_name_to_id[base_name]
        instance_index = base_name_index[base_name]
        model_id = f"{group_id}-{instance_index}"

        modelName2mbsID[model_key] = model_id
        mbsID2modelName[model_id] = model_key

        base_name_index[base_name] += 1

    return data

    
app = Dash(__name__)
app.title = "Conjecture Heatmap"
app = dash.Dash(__name__, suppress_callback_exceptions=True)

def get_conjecture_sections(data, model_cx, source='evalConj'):
    # Fix missing underscore before "cX"
    if re.match(r".+c\d+$", model_cx) and "_c" not in model_cx:
        model_cx = re.sub(r"c(\d+)$", r"_c\1", model_cx)
    
    match = re.match(r"([a-zA-Z_]+)(\d+)_c(\d+)", model_cx)
    if not match:
        return {"Error": f"Invalid format for model_cx: {model_cx}"}
    
    # model_cx = model_cx.replace("&", "_")  # ✅ sanitize any malformed cx input
    # match = re.match(r"([a-zA-Z_]+)(\d+)_c(\d+)", model_cx)
    if not match:
        return {"Error": f"Invalid format for model_cx: {model_cx}"}

    name = match.group(1)
    number = match.group(2)
    numberConj = int(match.group(3))
    modelName = name + number

    # Safely access all nested data
    model_data = data.get("allMbsModelsDict", {}).get(modelName, {})
    conj_data = model_data.get("conjectures", [{}])[numberConj] if numberConj < len(model_data.get("conjectures", [])) else {}
    exu_data = data.get("genExu", {}).get("resultsDicts", {}).get(modelName, {}).get("resultsPerConj", [{}])
    exu_entry = exu_data[numberConj] if numberConj < len(exu_data) else {}

    eval_data = data.get(source, {}).get("allModelsResultsDicts", {}).get(modelName, {}).get("conjecturesEvaluated", [{}])
    eval_entry = eval_data[numberConj] if numberConj < len(eval_data) else {}

    wm_data = data.get("evalConj_WM", {}).get("allModelsResultsDicts", {}).get(modelName, {}).get("conjecturesEvaluated", [{}])
    wm_entry = wm_data[numberConj] if numberConj < len(wm_data) else {}

    return {
        "Model Name": model_cx,
        "modelDescription": model_data.get("modelDescription", "[missing]"),
        "modelDescriptionWrong": model_data.get("modelDescription_wrong", "[missing]"),
        "evaluationMethod": conj_data.get("evaluationMethod", "[missing]"),
        "requiredSensors": str(conj_data.get("requiredSensors", "[missing]")),
        "conjecture": conj_data.get("conjecture", "[missing]"),
        "conjecture_wrong": conj_data.get("conjecture_wrong", "[missing]"),
        "exudynCode": exu_entry.get("exudynCode", "[missing]"),
        "modelIsCorrect": str(eval_entry.get("modelIsCorrect", "[missing]")),
        "simulationResults": exu_entry.get("simulationResults", "[missing]"),
        "conjPrompt": eval_entry.get("conjPrompt", "[missing]"),
        "scoreValue": str(eval_entry.get("scoreValue", "[missing]")),
        "conjPrompt_WM": wm_entry.get("conjPrompt", "[missing]"),
        "scoreValue_WM": str(wm_entry.get("scoreValue", "[missing]")),
    }    
    




def build_model_method_score_heatmap_plotly(data, evalMethod='average',includeIncorrectModels=False,visible_columns=None,visible_rows=None, highlighted_cell=None, model_label_mode="full"):
    binary_mode = evalMethod in ["relativeBinary", "binaryAverages"]
    
    def prepare_dataRelativeGoodnessScore(source,includeIncorrectModels=False):
        scores_dict = defaultdict(list)
        conj_labels = defaultdict(list)
        error_mask_solid = defaultdict(bool)
        error_mask_dashed = defaultdict(bool)
    
        models_eval = data.get("evalConj", {}).get("allModelsResultsDicts", {})
        models_wm = data.get("evalConj_WM", {}).get("allModelsResultsDicts", {})
    
        for model_key, model_val in models_eval.items():
            conj_evals = model_val.get("conjecturesEvaluated", [])
            wm_conj_evals = models_wm.get(model_key, {}).get("conjecturesEvaluated", [])
            original_conjs = data["allMbsModelsDict"].get(model_key, {}).get("conjectures", [])
    
            for i, conj_result in enumerate(conj_evals):
                conj_id = conj_result.get("currentMBSmodelNameIDcID", "")
                c_label = "?" if "c" not in conj_id else "c" + conj_id.split("c")[-1]
                scoreA = conj_result.get("scoreValue", None)
                model_correct = conj_result.get("modelIsCorrect", False)
                diff_llm = conj_result.get("differenceLLM", None)
    
                # Evaluation method label
                try:
                    method = original_conjs[i].get("evaluationMethod", "Unknown")
                except Exception:
                    method = "Unknown"
                   

                register_eval_method(method)
   
                key = (model_key, method)
                conj_labels[key].append(c_label)
    
                # Error flags
                if not model_correct:
                    error_mask_solid[key] = True
                elif isinstance(scoreA, (int, float)) and scoreA < 0:
                    error_mask_dashed[key] = True
    
                # Check if valid case for evaluation
                if (
                    not isinstance(scoreA, (int, float)) or
                    scoreA < 0 or scoreA > 1 or
                    diff_llm is None or
                    not isinstance(diff_llm, (int, float)) or
                    # diff_llm < 1e-5 or
                    (not includeIncorrectModels and not model_correct)
                ):

                    continue
    
                # Get corresponding WM score
                try:
                    scoreB = wm_conj_evals[i].get("scoreValue", None) if i < len(wm_conj_evals) else None
                    if scoreB is None or not isinstance(scoreB, (int, float)) or scoreB < 0 or scoreB > 1:
                        continue
    
                    y_ref = 1.
                    dA = abs(scoreA - y_ref)
                    dB = abs(scoreB - y_ref)
                    epsilon = 1e-8
                    
                    if abs(scoreA - scoreB) < 1e-8:
                        rel_score = 0.5
                    else:
                        rel_score = dB**2 / (dA**2 + dB**2 + epsilon)
                    
                    score_for_evalConj = rel_score
                    score_for_evalConj_WM = 1 - rel_score

                    # score_for_evalConj = 1 - abs(scoreA - 1.0)
                    # score_for_evalConj_WM = 1 - abs(scoreB - 1.0)    

                    # score_for_evalConj and score_for_evalConj_WM are already computed
                    if binary_mode:
                        # score_for_evalConj = 1 if score_for_evalConj >= 0.5 else 0
                        # score_for_evalConj_WM = 1 if score_for_evalConj_WM >= 0.5 else 0

                        if score_for_evalConj > 0.5:
                            score_for_evalConj = 1
                        elif score_for_evalConj == 0.5:
                            score_for_evalConj = 0.5
                        else:
                            score_for_evalConj = 0


                        if score_for_evalConj_WM > 0.5:
                            score_for_evalConj_WM = 1
                        elif score_for_evalConj_WM == 0.5:
                            score_for_evalConj_WM = 0.5
                        else:
                            score_for_evalConj_WM = 0
    
                    if source == "evalConj":
                        scores_dict[key].append(score_for_evalConj)
                    elif source == "evalConj_WM":
                        scores_dict[key].append(score_for_evalConj_WM)
    
                except Exception as e:
                    continue
    
        return scores_dict, conj_labels, error_mask_solid, error_mask_dashed
        
    
    
    
    def prepare_data(source,includeIncorrectModels=False):
        scores_dict = defaultdict(list)
        conj_labels = defaultdict(list)
        error_mask_solid = defaultdict(bool)
        error_mask_dashed = defaultdict(bool)

        models = data.get(source, {}).get("allModelsResultsDicts", {})
        for model_key, model_val in models.items():
            conj_evals = model_val.get("conjecturesEvaluated", [])
            original_conjs = data["allMbsModelsDict"][model_key]["conjectures"]

            for i, conj_result in enumerate(conj_evals):
                score = conj_result.get("scoreValue", None)
                model_correct = conj_result.get("modelIsCorrect", False)
                diff_llm = conj_result.get("differenceLLM", 1.0)
                

                conj_id = conj_result.get("currentMBSmodelNameIDcID", "")
                c_label = "?" if "c" not in conj_id else "c" + conj_id.split("c")[-1]

                try:
                    method = original_conjs[i]["evaluationMethod"]
                except:
                    method = "Unknown"


                register_eval_method(method)

                key = (model_key, method)
                conj_labels[key].append(c_label)

                if not model_correct:
                    error_mask_solid[key] = True
                elif isinstance(score, (int, float)) and score < 0:
                    error_mask_dashed[key] = True

                if (
                    isinstance(score, (int, float)) and
                    0 <= score <= 1 and
                    # diff_llm <= 1e-5 and
                    (includeIncorrectModels or model_correct)
                ):
                    scores_dict[key].append(score)

        return scores_dict, conj_labels, error_mask_solid, error_mask_dashed

    def build_single_heatmap(scores_dict, conj_labels, error_mask_solid, error_mask_dashed, title, xref="x", yref="y", evalMethod="raw", model_label_mode="full"):
        all_keys = set(scores_dict.keys()) | set(error_mask_solid.keys()) | set(error_mask_dashed.keys())
        # all_models = sorted(set(k[0] for k in all_keys))
        
        all_models = list(set(k[0] for k in all_keys))
        
        def sort_key(model):
            id_str = modelName2mbsID.get(model, "999-999")
            parts = id_str.split("-")
            return (int(parts[0]), int(parts[1])) if len(parts) == 2 else (999, 999)
        
        all_models.sort(key=sort_key)        
        all_models = all_models[::-1]
        
        if visible_rows:
            all_models = [m for m in all_models if m in visible_rows]
        # all_methods = sorted(set(k[1] for k in all_keys))
        # if visible_columns:
        #     all_methods = [m for m in all_methods if m in visible_columns]

        # Build list and sort by method ID
        all_methods = list(set(k[1] for k in all_keys))
        if visible_columns:
            all_methods = [m for m in all_methods if m in visible_columns]
        # Always sort using ID, regardless of display mode
        all_methods.sort(key=lambda m: evalMethod2ID.get(m, float("inf")))

            
        df = pd.DataFrame(index=all_models, columns=all_methods)
        label_df = pd.DataFrame(index=all_models, columns=all_methods)

        
        for (model, method), values in scores_dict.items():
            if visible_columns and method not in visible_columns:
                continue
            if visible_rows and model not in visible_rows:
                continue
            df.loc[model, method] = np.mean(values)
        
            
        for (model, method), labels in conj_labels.items():
            if visible_columns and method not in visible_columns:
                continue
            if visible_rows and model not in visible_rows:
                continue
            label_df.loc[model, method] = ", ".join(sorted(set(labels)))

        df_numeric = df.apply(pd.to_numeric, errors='coerce')


         
        # Exclude summary rows and columns
        original_columns = [col for col in df_numeric.columns if col not in ["Sum", "Average"]]
        original_rows = [idx for idx in df_numeric.index if idx not in ["Sum", "Average"]]
        
        # Compute row and column averages safely from the core
        core_df = df_numeric.loc[original_rows, original_columns]
        
        row_avg = core_df.mean(axis=1)
        col_avg = core_df.mean(axis=0)




        if evalMethod in ["relativeBinary", "binaryAverages"]:
            # Binary mode: leave original df_numeric untouched!
            df_display = df_numeric.applymap(lambda val: 1.0 if pd.notna(val) and val >= 0.5 else 0.0 if pd.notna(val) else np.nan)
        else:
            df_display = df_numeric.copy()
        
        
        if evalMethod == "binaryAverages":       
            # Then binarize the averages again
            row_avg_bin = row_avg.apply(lambda x: 1.0 if pd.notna(x) and x >= 0.5 else 0.0 if pd.notna(x) else np.nan)
            col_avg_bin = col_avg.apply(lambda x: 1.0 if pd.notna(x) and x >= 0.5 else 0.0 if pd.notna(x) else np.nan)
        
            df.loc[original_rows, "Average"] = row_avg_bin
            df.loc["Average", original_columns] = col_avg_bin
        else:
            df.loc[original_rows, "Average"] = row_avg
            df.loc["Average", original_columns] = col_avg
        
        # --- Compute and assign sums (same for all modes) ---
        df["Sum"] = df_numeric.sum(axis=1).where(df_numeric.notna().any(axis=1), np.nan)
        col_sum = df_numeric.sum(axis=0).where(df_numeric.notna().any(axis=0), np.nan)
        df.loc["Sum", original_columns] = col_sum
        
        # --- Reorder summary rows and columns to switch Sum and Average ---
        row_order = [r for r in df.index if r not in ["Average", "Sum"]] + ["Sum", "Average"]

        
        col_order = [c for c in df.columns if c not in ["Average", "Sum"]] + ["Sum", "Average"]
        
        df = df.loc[row_order, col_order]
        label_df = label_df.reindex(index=row_order, columns=col_order)
        
        # Make sure label_df is padded
        for row in ["Sum", "Average"]:
            if row not in label_df.index:
                label_df.loc[row] = ""
        
        # Now compute 2×2 corner values
        original_rows = [idx for idx in df.index if idx not in ["Sum", "Average"]]
        original_cols = [col for col in df.columns if col not in ["Sum", "Average"]]
        core_values = df_numeric.loc[original_rows, original_cols]
        
                
        # Recompute corner 2x2 values correctly
        corner_avg_row = df.loc["Average", original_columns].mean()
        corner_avg_col = df.loc[original_rows, "Average"].mean()
        
        corner_center  = (corner_avg_row + corner_avg_col) / 2
        
        # df.loc["Sum", "Sum"]         = corner_avg_row
        df.loc["Average", "Average"] = corner_center
        
        df.loc["Sum", "Average"]     = corner_avg_col
        df.loc["Average", "Sum"]     = corner_avg_row

        for row in ["Sum", "Average"]:
            if row not in label_df.index:
                label_df.loc[row] = ""


        # Define core columns (excluding summary and dummy ones)
        core_columns = [col for col in df_numeric.columns if col not in ["Sum", "Average", "TEST", "ProductScore"]]
        core_rows = [idx for idx in df_numeric.index if idx not in ["Sum", "Average"]]
        
        def safe_product(series, use_one_minus=False):
            values = series[core_columns].dropna()
            if use_one_minus:
                values = values
            if values.empty:
                return np.nan
            prod = np.prod(values)
            return prod if np.isfinite(prod) else np.nan
        
        # Determine whether to flip scores based on the heatmap title
        use_one_minus = (title == "evalConj_WM")
        
        # Compute and assign product per row
        df["ProductScore"] = np.nan  # Ensure column exists
        for idx in core_rows:
            df.loc[idx, "ProductScore"] = safe_product(df.loc[idx], use_one_minus=use_one_minus)
        label_df["ProductScore"] = ""    

        # --- Compute Incorrect Count per model based on visible values only ---
        df["Incorrect Count"] = np.nan
        
        for model in core_rows:
            if title == "evalConj":
                # Count how many 0.0s are in the row (ignore NaN)
                count = (df_numeric.loc[model, core_columns] == 0.0).sum()
            elif title == "evalConj_WM":
                # Count how many 1.0s are in the row (ignore NaN)
                count = (df_numeric.loc[model, core_columns] == 1.0).sum()
            else:
                count = np.nan
        
            df.loc[model, "Incorrect Count"] = count
        
        label_df["Incorrect Count"] = ""
        
        # --- Add new column for adjusted row average with override logic ---
        adjusted_col_label = "Avg+Rule"
        
        adjusted_col = pd.Series(index=original_rows, dtype=float)
        
        for model in original_rows:
            row_values = core_df.loc[model].dropna()
        
            if title == "evalConj":
                zero_count = (row_values == 0.0).sum()
                if zero_count >= 2:
                    adjusted_col[model] = 0.0
                else:
                    adjusted_col[model] = row_avg[model]
        
            elif title == "evalConj_WM":
                one_count = (row_values == 1.0).sum()
                if one_count >= 2:
                    adjusted_col[model] = 1.0
                else:
                    adjusted_col[model] = row_avg[model]
        
        # Add the column to df
        df[adjusted_col_label] = adjusted_col
        label_df[adjusted_col_label] = ""

        
        # Recompute the display matrix to include it
        df_numeric = df.apply(pd.to_numeric, errors='coerce')  # Refresh numeric values



        col_order = [c for c in df.columns if c not in ["Average", "Sum", "Avg+Rule","ProductScore","Incorrect Count"]] + ["Sum", "Average","Avg+Rule","ProductScore","Incorrect Count"]
        df = df.loc[row_order, col_order]
        label_df = label_df.reindex(index=row_order, columns=col_order)

        z_vals = df.values.astype(float)
        x_vals = df.columns.tolist()
        
        # Display mapping for column (method) labels
        if model_label_mode == "id":
            x_vals_display = []
            method_display_map = {}
            for m in x_vals:
                if m in evalMethod2ID:
                    label = f"{evalMethod2ID[m]}"
                    x_vals_display.append(label)
                    method_display_map[label] = m
                else:
                    x_vals_display.append(m)
                    method_display_map[m] = m
        else:
            x_vals_display = x_vals
            method_display_map = {m: m for m in x_vals}

        y_vals = df.index.tolist()
        

        
        # === Compute display labels (ID format or full name) ===
        model_display_map = {}  # maps display label → real model name
        

        # === Compute display labels (ID format or full name) ===
        if model_label_mode == "id":
            y_vals_display = [modelName2mbsID.get(m, "?") for m in y_vals]
            model_display_map = dict(zip(y_vals_display, y_vals))
        else:
            y_vals_display = y_vals
            model_display_map = {m: m for m in y_vals}



        text_grid = []
        custom_data = []
        for model in y_vals:
            text_row = []
            data_row = []
            for method in x_vals:
                real_col = method_display_map.get(method, method) if model_label_mode == "id" else method
                val = df.loc[model, real_col]
                label = label_df.loc[model, real_col] if real_col in label_df.columns else ""
                if pd.isna(val) and pd.isna(label):
                    text_row.append("")
                    data_row.append("")
                else:
                    display_score = f"{val:.2f}" if pd.notna(val) and val >= 0 else "N.N."
                    label_str = f"<br>{label}" if pd.notna(label) and label != "" else ""
                    text_row.append(f"{display_score}{label_str}")
                    first_cx = str(label).split(",")[0].strip() if pd.notna(label) else "?"
                    model_cx = f"{model}_{first_cx}"
                    data_row.append(f"{model}|{method}|{title}|{model_cx}")
            text_grid.append(text_row)
            custom_data.append(data_row)

        heatmap = go.Heatmap(
            z=z_vals,
            x=x_vals_display,
            y=y_vals_display,
            text=text_grid,
            hovertemplate='Score: %{z:.6f}<extra></extra>',  # 6 decimal places
            hoverinfo="text",
            texttemplate="%{text}",
            colorscale="YlGnBu",
            zmin=0, zmax=1,
            colorbar=dict(title="Mean Score"),
            showscale=True,
            name=title,
            customdata=custom_data
        )

        shapes = []
        for i, model in enumerate(y_vals_display):
            for j, method in enumerate(x_vals):
                shapes.append(dict(
                    type="rect",
                    x0=j - 0.5, x1=j + 0.5,
                    y0=i - 0.5, y1=i + 0.5,
                    line=dict(color="black", width=0.5),
                    xref=xref, yref=yref,
                    layer="below"
                ))

        for (model, method), _ in error_mask_solid.items():
            if method not in x_vals or model not in y_vals:
                continue
            i = y_vals.index(model)
            j = x_vals.index(method)
            shapes.append(dict(
                type="rect",
                x0=j - 0.5, x1=j + 0.5,
                y0=i - 0.5, y1=i + 0.5,
                line=dict(color="red", width=2),
                xref=xref, yref=yref,
                layer="above"
            ))

        for (model, method), _ in error_mask_dashed.items():
            if method not in x_vals or model not in y_vals:
                continue
            i = y_vals.index(model)
            j = x_vals.index(method)
            shapes.append(dict(
                type="rect",
                x0=j - 0.5, x1=j + 0.5,
                y0=i - 0.5, y1=i + 0.5,
                line=dict(color="red", width=2, dash='dash'),
                xref=xref, yref=yref,
                layer="above"
            ))


         # === RED OUTLINE around the core block (excluding summary rows/cols) ===
        if "Sum" in x_vals and "Average" in x_vals and "Sum" in y_vals and "Average" in y_vals:
             # Determine limits of core grid (before summary rows/cols)
             last_core_col_idx = x_vals.index("Sum") - 1
             last_core_row_idx = y_vals.index("Sum") - 1
         
             shapes.append(dict(
                 type="rect",
                 x0=-0.5,
                 x1=last_core_col_idx + 0.5,
                 y0=-0.5,
                 y1=last_core_row_idx + 0.5,
                 line=dict(color="limegreen", width=4),
                 xref=xref, yref=yref,
                 layer="above"
             ))
        

        annotations = []
        if highlighted_cell:
            h_model = highlighted_cell.get("model")
            h_method = highlighted_cell.get("method")
            h_source = highlighted_cell.get("source")
        
            is_active = title == h_source
            color = "magenta" if is_active else "royalblue"


        
            if h_model in y_vals and h_method in x_vals:
               i = y_vals.index(h_model)
               j = x_vals.index(h_method)
               
               # Highlight box — always magenta
               shapes.append(dict(
                   type="rect",
                   x0=j - 0.5, x1=j + 0.5,
                   y0=i - 0.5, y1=i + 0.5,
                   line=dict(color="magenta", width=4),
                   xref=xref, yref=yref,
                   layer="above"
               ))

               # Highlight full row (excluding summary cols like "Sum", "Average", etc.)
               for jx, col_name in enumerate(x_vals):
                    if col_name in ["Sum", "Average", "Avg+Rule", "ProductScore", "Incorrect Count"]:
                        continue
                    shapes.append(dict(
                        type="rect",
                        x0=jx - 0.5, x1=jx + 0.5,
                        y0=i - 0.5, y1=i + 0.5,
                        line=dict(color="magenta", width=1.5, dash="dot"),
                        xref=xref, yref=yref,
                        layer="above"
                    ))
                
               # Highlight full column (excluding summary rows)
               for iy, row_name in enumerate(y_vals):
                    if row_name in ["Sum", "Average"]:
                        continue
                    shapes.append(dict(
                        type="rect",
                        x0=j - 0.5, x1=j + 0.5,
                        y0=iy - 0.5, y1=iy + 0.5,
                        line=dict(color="magenta", width=1.5, dash="dot"),
                        xref=xref, yref=yref,
                        layer="above"
                    ))


               # --- Highlight entire row (horizontal stripe) ---
               shapes.append(dict(
                    type="rect",
                    x0=-0.5,
                    x1=len(x_vals) - 0.5,
                    y0=i - 0.5,
                    y1=i + 0.5,
                    fillcolor="magenta",
                    opacity=0.12,
                    line=dict(width=0),
                    xref=xref,
                    yref=yref,
                    layer="below"
                ))
                
                # --- Highlight entire column (vertical stripe) ---
               shapes.append(dict(
                    type="rect",
                    x0=j - 0.5,
                    x1=j + 0.5,
                    y0=-0.5,
                    y1=len(y_vals) - 0.5,
                    fillcolor="magenta",
                    opacity=0.12,
                    line=dict(width=0),
                    xref=xref,
                    yref=yref,
                    layer="below"
                ))



               
               # Arrow — only on clicked source
               if title == h_source:
                   annotations.append(dict(
                       x=j + 0.5, y=i,
                       ax=j + 1.2, ay=i,
                       xref=xref, yref=yref,
                       axref=xref, ayref=yref,
                       text="",
                       showarrow=True,
                       arrowhead=3,
                       arrowsize=1.2,
                       arrowwidth=2,
                       arrowcolor="magenta",
                   ))

                


        return heatmap, shapes, x_vals, y_vals, df_numeric, core_rows, annotations, label_df

    # Prepare data
    if evalMethod in ["relativeGoodnessScore", "relativeBinary", "binaryAverages"]:
        left_scores, left_labels, left_err_solid, left_err_dashed = prepare_dataRelativeGoodnessScore("evalConj",includeIncorrectModels=includeIncorrectModels)
        right_scores, right_labels, right_err_solid, right_err_dashed = prepare_dataRelativeGoodnessScore("evalConj_WM",includeIncorrectModels=includeIncorrectModels)
        
        
    else:  
        left_scores, left_labels, left_err_solid, left_err_dashed = prepare_data("evalConj",includeIncorrectModels=includeIncorrectModels)
        right_scores, right_labels, right_err_solid, right_err_dashed = prepare_data("evalConj_WM",includeIncorrectModels=includeIncorrectModels)
        
        
    heatmap1, shapes1, x1, y1, df_numeric1, core_rows1, annotations1, label_df1 = build_single_heatmap(
        left_scores, left_labels, left_err_solid, left_err_dashed, "evalConj", 
        xref="x1", yref="y1", evalMethod=evalMethod, model_label_mode=model_label_mode
    )
    heatmap2, shapes2, x2, y2, df_numeric2, core_rows2, annotations2, label_df2 = build_single_heatmap(
        right_scores, right_labels, right_err_solid, right_err_dashed, "evalConj_WM", 
        xref="x2", yref="y2", evalMethod=evalMethod, model_label_mode=model_label_mode
    )
    
    # export_core_heatmap_to_pdf(df_numeric1, label_df1, filename="core_block.pdf")
    
    # Compute summary stats based on left/right heatmap's data (evalConj)
    try:
        avg_average1 = df_numeric1.loc[core_rows1, "Average"].mean()
        avg_avg_rule1 = df_numeric1.loc[core_rows1, "Avg+Rule"].mean()
        avg_product1 = df_numeric1.loc[core_rows1, "ProductScore"].mean()
        
        avg_average2 = df_numeric2.loc[core_rows2, "Average"].mean()
        avg_avg_rule2 = df_numeric2.loc[core_rows2, "Avg+Rule"].mean()
        avg_product2 = df_numeric2.loc[core_rows2, "ProductScore"].mean()
        
        summary_stats_text = (
            f"<b>evalConj (left):</b><br>"
            f"Average (mean of rows): {avg_average1:.3f}  "
            f"Avg+Rule: {avg_avg_rule1:.3f}  "
            f"Product Score: {avg_product1:.3f}<br><br>"
            f"<b>evalConj_WM (right):</b><br>"
            f"Average (mean of rows): {avg_average2:.3f}  "
            f"Avg+Rule: {avg_avg_rule2:.3f}  "
            f"Product Score: {avg_product2:.3f}"
        )
    except Exception:
        summary_stats_text = ""

    fig = make_subplots(rows=1, cols=2, subplot_titles=("evalConj", "evalConj_WM"), shared_yaxes=True,horizontal_spacing=0.02)
    fig.add_trace(heatmap1, row=1, col=1)
    fig.add_trace(heatmap2, row=1, col=2)

    fig.update_layout(
        title="Click a cell to export full conjecture text<br><span style='font-size:12px'>Mean Score per (Model × Evaluation Method)<br>Solid = model incorrect, Dashed = score < 0 | Labels = cX IDs</span>",
        height=1600,
        margin=dict(l=100, r=100, t=100, b=100),
        font=dict(size=11),
        shapes=shapes1 + shapes2,
        
        annotations=[
            dict(
                text=summary_stats_text,
                xref="paper",
                yref="paper",
                x=0.5,
                y=1.07,
                xanchor="center",
                yanchor="top",
                showarrow=False,
                font=dict(size=14)
            )
        ] + annotations1 + annotations2        
            
    )
    fig.update_yaxes(type='category', row=1, col=1)
    fig.update_yaxes(type='category', row=1, col=2)

    return fig, df_numeric1, label_df1, df_numeric2, label_df2




def build_best_worst_model_plot(data, source="evalConj"):
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    models = data[source]["allModelsResultsDicts"]
    scores = {}

    for model_key, model_val in models.items():
        conj_evals = model_val.get("conjecturesEvaluated", [])
        valid_scores = []

        for result in conj_evals:
            score = result.get("scoreValue")
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                valid_scores.append(score)

        if valid_scores:
            scores[model_key] = np.mean(valid_scores)

    df = pd.Series(scores).sort_values(ascending=False)

    top_n = 10
    top_models = df.head(top_n)
    bottom_models = df.tail(top_n)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=top_models.values,
        y=top_models.index,
        name="Top Models",
        orientation="h",
        marker_color="green"
    ))

    fig.add_trace(go.Bar(
        x=bottom_models.values,
        y=bottom_models.index,
        name="Bottom Models",
        orientation="h",
        marker_color="red"
    ))

    fig.update_layout(
        title=f"Top and Bottom {top_n} Models by Mean Score ({source})",
        xaxis_title="Mean Score",
        yaxis_title="Model Name",
        barmode="overlay",
        height=600
    )

    return fig


def build_best_worst_model_plot_dual(data):
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    from plotly.subplots import make_subplots

    def compute_scores(source):
        models = data[source]["allModelsResultsDicts"]
        scores = {}
        for model_key, model_val in models.items():
            conj_evals = model_val.get("conjecturesEvaluated", [])
            valid_scores = []
            for result in conj_evals:
                score = result.get("scoreValue")
                if isinstance(score, (int, float)) and 0 <= score <= 1:
                    valid_scores.append(score)
            if valid_scores:
                scores[model_key] = np.mean(valid_scores)
        return pd.Series(scores).sort_values(ascending=False)

    df1 = compute_scores("evalConj")
    df2 = compute_scores("evalConj_WM")

    top_n = 10
    fig = make_subplots(rows=1, cols=2, shared_yaxes=False, horizontal_spacing=0.15,
                        subplot_titles=["Top/Bottom Models (evalConj)", "Top/Bottom Models (evalConj_WM)"])

    # evalConj
    fig.add_trace(go.Bar(
        x=df1.head(top_n).values,
        y=df1.head(top_n).index,
        name="Top Models (evalConj)",
        orientation="h",
        marker_color="green"
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df1.tail(top_n).values,
        y=df1.tail(top_n).index,
        name="Bottom Models (evalConj)",
        orientation="h",
        marker_color="red"
    ), row=1, col=1)

    # evalConj_WM
    fig.add_trace(go.Bar(
        x=df2.head(top_n).values,
        y=df2.head(top_n).index,
        name="Top Models (evalConj_WM)",
        orientation="h",
        marker_color="green"
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=df2.tail(top_n).values,
        y=df2.tail(top_n).index,
        name="Bottom Models (evalConj_WM)",
        orientation="h",
        marker_color="red"
    ), row=1, col=2)

    fig.update_layout(
        title="Top and Bottom Models by Mean Score (Side-by-Side)",
        height=700,
        width=1400,
        showlegend=True
    )

    return fig



def build_aligned_model_comparison_plot(data):
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    def get_model_scores_and_flags(source):
        models = data[source]["allModelsResultsDicts"]
        scores = {}
        error_flags = {}

        for model_key, model_val in models.items():
            conj_evals = model_val.get("conjecturesEvaluated", [])
            valid_scores = []
            has_error = False

            for res in conj_evals:
                score = res.get("scoreValue")
                correct = res.get("modelIsCorrect", True)

                if isinstance(score, (int, float)) and 0 <= score <= 1:
                    valid_scores.append(score)
                if (isinstance(score, (int, float)) and score < 0) or (correct is False):
                    has_error = True

            if valid_scores:
                scores[model_key] = np.mean(valid_scores)
            if has_error:
                error_flags[model_key] = 1

        return scores, error_flags

    scores_evalConj, errors_evalConj = get_model_scores_and_flags("evalConj")
    scores_evalConj_WM, errors_evalConj_WM = get_model_scores_and_flags("evalConj_WM")

    all_models = sorted(set(scores_evalConj) | set(scores_evalConj_WM))
    evalConj_scores = pd.Series(scores_evalConj, index=all_models)
    evalConj_WM_scores = pd.Series(scores_evalConj_WM, index=all_models)

    error_flags = pd.Series(0, index=all_models)
    for m in errors_evalConj:
        error_flags[m] = 1
    for m in errors_evalConj_WM:
        error_flags[m] = 1

    # Sort by evalConj score
    sorted_models = evalConj_scores.sort_values(ascending=False).index
    evalConj_scores = evalConj_scores[sorted_models]
    evalConj_WM_scores = evalConj_WM_scores[sorted_models]
    error_flags = error_flags[sorted_models]

    # Y axis spacing — extra vertical space between rows
    spacing = 1.5  # increase for more spacing
    base_y = np.arange(len(sorted_models)) * spacing
    y_offset_green = base_y + 0.3
    y_offset_blue = base_y
    y_offset_red = base_y - 0.3

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=evalConj_scores.values,
        y=y_offset_green,
        orientation="h",
        name="evalConj (high = good)",
        marker_color="green",
        width=0.5,
        hovertemplate="%{x:.2f}",
    ))

    fig.add_trace(go.Bar(
        x=evalConj_WM_scores.values,
        y=y_offset_blue,
        orientation="h",
        name="evalConj_WM (low = good)",
        marker_color="blue",
        width=0.5,
        hovertemplate="%{x:.2f}",
    ))

    fig.update_layout(
        xaxis=dict(
            title="Mean Score",
            tickmode="array",
            tickvals=[0.0, 0.25, 0.5, 0.75, 1.0],
            ticktext=["0", "0.25", "0.5", "0.75", "1.0"],
            tickfont=dict(size=25)  # Optional: make tick labels bigger
        )
    )
    fig.update_layout(
        title="evalConj vs. evalConj_WM – Top/Bottom Models Aligned<br><span style='font-size:12px'>↑ Top = Best models (Green: high score, Blue: low score, Red = error)</span>",
        xaxis_title="Mean Score",
        yaxis=dict(
            tickmode="array",
            tickvals=base_y,
            ticktext=evalConj_scores.index.tolist(),
            title="Model Name"
        ),
        barmode="overlay",
        bargap=0.25,
        height=spacing * len(sorted_models) * 30 + 200,  # dynamic height
        margin=dict(l=180, r=40, t=100, b=60),
        font=dict(size=20)
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    
    ymin = -1
    ymax = len(base_y)+17
    
    x_positions = np.arange(0, 1.05, 0.25)
    
    for x in x_positions:
        fig.add_shape(
            type="line",
            x0=x, x1=x,
            y0=ymin, y1=ymax,
            line=dict(color="black", width=5, dash="dash"),
            xref="x",
            yref="y",
            layer="below"
        )



    fig.update_layout(yaxis=dict(autorange="reversed", range=[ymin, ymax]))
    
    return fig

def export_core_heatmap_to_pdf(df_numeric, label_df, filename="core_heatmap.pdf"):
    """
    Export just the core green block (model × method cells) of the heatmap to a PDF.

    Parameters:
    - df_numeric: DataFrame with numeric values (model × method).
    - label_df: DataFrame with label overlays (same shape as df_numeric).
    - filename: Output PDF file name.
    """

    # Identify core (non-summary) rows and columns
    core_rows = [idx for idx in df_numeric.index if idx not in ["Sum", "Average"]]
    core_cols = [col for col in df_numeric.columns if col not in ["Sum", "Average", "Avg+Rule", "ProductScore", "Incorrect Count"]]

    # Subset the DataFrames
    z_vals = df_numeric.loc[core_rows, core_cols].values.astype(float)
    text_vals = label_df.loc[core_rows, core_cols].copy()

    # Format text overlay
    for row in text_vals.index:
        for col in text_vals.columns:
            val = df_numeric.loc[row, col]
            label = label_df.loc[row, col]
            display_score = f"{val:.2f}" if pd.notna(val) and val >= 0 else "N.N."
            label_str = f"<br>{label}" if pd.notna(label) and label != "" else ""
            text_vals.loc[row, col] = f"{display_score}{label_str}"

    # Build heatmap figure
    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=core_cols,
        y=core_rows,
        text=text_vals.values,
        texttemplate="%{text}",
        hoverinfo="text",
        colorscale="YlGnBu",
        zmin=0, zmax=1,
        colorbar=dict(title="Score"),
        showscale=True
    ))

    fig.update_layout(
        title="Core Heatmap Block (Model × Evaluation Method)",
        height=35 * len(core_rows) + 100,
        width=60 * len(core_cols) + 200,
        margin=dict(l=120, r=40, t=60, b=40),
        font=dict(size=11)
    )

    import plotly.io as pio
    pio.orca.config.use_xvfb = True  # only needed on headless servers
    pio.write_image(fig, "output.svg", format="svg", engine="orca")
    
def build_horizontal_stacked_score_plot(data, source="evalConj"):
    import plotly.graph_objects as go
    import numpy as np
    from collections import defaultdict

    method_names = {}  # (model_key, conj_index) → evaluationMethod
    score_bins = defaultdict(lambda: {"low": 0, "high": 0, "bad": 0})

    # Step 1: Extract method names
    for model_key, model_data in data.get("allMbsModelsDict", {}).items():
        for i, conj in enumerate(model_data.get("conjectures", [])):
            method = conj.get("evaluationMethod", "Unknown")
            method_names[(model_key, i)] = method

    # Step 2: Fill bins from evalConj
    models = data.get(source, {}).get("allModelsResultsDicts", {})
    for model_key, model_val in models.items():
        for i, conj_result in enumerate(model_val.get("conjecturesEvaluated", [])):
            score = conj_result.get("scoreValue", None)
            method = method_names.get((model_key, i), "Unknown")
            model_correct = conj_result.get("modelIsCorrect", False)
            diff_llm = conj_result.get("differenceLLM", 1.0)

            if model_correct and diff_llm == 0 and score != -100:
                if score is not None:
                    if score < 0.5:
                        score_bins[method]["low"] += 1
                    else:
                        score_bins[method]["high"] += 1
            elif not model_correct:
                score_bins[method]["bad"] += 1

    # Step 3: Organize and sort
    sorted_methods = sorted(score_bins.items(), key=lambda x: x[1]["high"], reverse=True)
    methods = [m[0] for m in sorted_methods]
    high_scores = [m[1]["high"] for m in sorted_methods]
    low_scores = [m[1]["low"] for m in sorted_methods]
    bad_scores = [m[1]["bad"] for m in sorted_methods]
    
    # Use spaced base values for vertical bar positions
    y_vals = np.arange(0, len(methods) * 1.3, 2)  # This adds spacing between methods
    offset = 0.3
    y_high = y_vals + offset
    y_low = y_vals
    y_bad = y_vals - offset

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=high_scores,
        y=y_high,
        name="Score ≥ 0.5 (correct, diff=0)",
        orientation="h",
        marker_color="orange",
        width=0.8,
        hovertemplate="High Score: %{x}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=low_scores,
        y=y_low,
        name="Score < 0.5 (correct, diff=0)",
        orientation="h",
        marker_color="blue",
        width=0.8,
        hovertemplate="Low Score: %{x}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=bad_scores,
        y=y_bad,
        name="Incorrect (bad)",
        orientation="h",
        marker_color="red",
        width=0.8,
        hovertemplate="Incorrect: %{x}<extra></extra>"
    ))

    fig.update_layout(
        title="Evaluation Methods – Score Breakdown per Conjecture Type<br><span style='font-size:12px'>Orange = high score, Blue = low score, Red = incorrect</span>",
        xaxis_title="Number of Conjectures",
        yaxis=dict(
            tickmode="array",
            tickvals=y_vals,
            ticktext=methods,
            title="Evaluation Method",
            automargin=True
        ),
        barmode="overlay",
        height=800,
        margin=dict(l=300, r=40, t=100, b=60),
        font=dict(size=12)
    )
    fig.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=y_vals,
            ticktext=methods,
            title="Evaluation Method",
        )
    )
    return fig

def build_horizontal_stacked_score_comparison_plot(data):
    def collect_scores(source):
        bins = defaultdict(lambda: {"low": 0, "high": 0, "bad": 0})
        method_names = {}
        for model_key, model_data in data.get("allMbsModelsDict", {}).items():
            for i, conj in enumerate(model_data.get("conjectures", [])):
                method = conj.get("evaluationMethod", "Unknown")
                method_names[(model_key, i)] = method

        models = data.get(source, {}).get("allModelsResultsDicts", {})
        for model_key, model_val in models.items():
            for i, conj_result in enumerate(model_val.get("conjecturesEvaluated", [])):
                score = conj_result.get("scoreValue", None)
                method = method_names.get((model_key, i), "Unknown")
                model_correct = conj_result.get("modelIsCorrect", False)
                diff_llm = conj_result.get("differenceLLM", 1.0)

                if model_correct and diff_llm < 1e-6 and score != -100:
                    if isinstance(score, (float, int)):
                        if score < 0.5:
                            bins[method]["low"] += 1
                        else:
                            bins[method]["high"] += 1
                elif not model_correct:
                    bins[method]["bad"] += 1

        return bins

    # Collect scores
    bins_conj = collect_scores("evalConj")
    bins_wm = collect_scores("evalConj_WM")

    # Use all methods, sorted by evalConj high scores
    all_methods = sorted(bins_conj.keys(), key=lambda m: bins_conj[m]["high"], reverse=True)

    high_c = [bins_conj[m]["high"] for m in all_methods]
    low_c = [bins_conj[m]["low"] for m in all_methods]
    bad_c = [bins_conj[m]["bad"] for m in all_methods]

    high_w = [bins_wm[m]["high"] for m in all_methods]
    low_w = [bins_wm[m]["low"] for m in all_methods]
    bad_w = [bins_wm[m]["bad"] for m in all_methods]

    y_vals = np.arange(0, len(all_methods) * 1.3, 2)
    offset = 0.3
    y_high = y_vals + offset
    y_low = y_vals
    y_bad = y_vals - offset

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.02,
                        subplot_titles=("evalConj", "evalConj_WM"))

    # Left: evalConj
    fig.add_trace(go.Bar(x=high_c, y=y_high, orientation="h", name="High (conj)", marker_color="orange", width=0.8), row=1, col=1)
    fig.add_trace(go.Bar(x=low_c, y=y_low, orientation="h", name="Low (conj)", marker_color="blue", width=0.8), row=1, col=1)
    fig.add_trace(go.Bar(x=bad_c, y=y_bad, orientation="h", name="Bad (conj)", marker_color="red", width=0.8), row=1, col=1)

    # Right: evalConj_WM
    fig.add_trace(go.Bar(x=high_w, y=y_high, orientation="h", name="High (WM)", marker_color="orange", opacity=0.5, width=0.8), row=1, col=2)
    fig.add_trace(go.Bar(x=low_w, y=y_low, orientation="h", name="Low (WM)", marker_color="blue", opacity=0.5, width=0.8), row=1, col=2)
    fig.add_trace(go.Bar(x=bad_w, y=y_bad, orientation="h", name="Bad (WM)", marker_color="red", opacity=0.5, width=0.8), row=1, col=2)

    fig.update_layout(
        barmode="overlay",
        height=900,
        margin=dict(l=300, r=40, t=80, b=60),
        font=dict(size=12),
        title="Evaluation Methods – Score Breakdown (Side-by-Side)"
    )

    fig.update_yaxes(
        tickmode="array", tickvals=y_vals, ticktext=all_methods,
        title="Evaluation Method", row=1, col=1
    )
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    fig.update_xaxes(title="Number of Conjectures", row=1, col=1)
    fig.update_xaxes(title="Number of Conjectures", row=1, col=2)

    return fig






from plotly.subplots import make_subplots


def plot_scores_grouped_by_model_name_with_wm_plotly(data):
    def collect_scores(source):
        bins = defaultdict(lambda: {"low": 0, "high": 0, "bad": 0})
        models = data.get(source, {}).get("allModelsResultsDicts", {})

        for model_key, model_val in models.items():
            for conj_result in model_val.get("conjecturesEvaluated", []):
                score = conj_result.get("scoreValue", None)
                model_correct = conj_result.get("modelIsCorrect", False)
                diff_llm = conj_result.get("differenceLLM", 1.0)

                if model_correct and diff_llm < 1e-6 and isinstance(score, (float, int)) and 0 <= score <= 1:
                    if source == "evalConj":
                        if score < 0.5:
                            bins[model_key]["low"] += 1
                        else:
                            bins[model_key]["high"] += 1
                    elif source == "evalConj_WM":
                        if score > 0.5:
                            bins[model_key]["high"] += 1
                        else:
                            bins[model_key]["low"] += 1
                else:
                    bins[model_key]["bad"] += 1

        return bins

    # Collect score bins
    bins_conj = collect_scores("evalConj")
    bins_wm = collect_scores("evalConj_WM")

    # Merge all model names
    all_models = sorted(set(bins_conj) | set(bins_wm))
    
    # Sort by high scores in evalConj
    sorted_models = sorted(all_models, key=lambda m: bins_conj.get(m, {}).get("high", 0), reverse=True)

    # Get counts
    def get_counts(bins, keys):
        high = [bins.get(k, {}).get("high", 0) for k in keys]
        low = [bins.get(k, {}).get("low", 0) for k in keys]
        bad = [bins.get(k, {}).get("bad", 0) for k in keys]
        return high, low, bad

    high_c, low_c, bad_c = get_counts(bins_conj, sorted_models)
    high_w, low_w, bad_w = get_counts(bins_wm, sorted_models)

    fig = go.Figure()

    # Horizontal bar stacking with slight vertical shifts
    base_y = list(range(len(sorted_models)))
    y_conj = [y + 0.2 for y in base_y]
    y_wm = [y - 0.2 for y in base_y]

    fig.add_trace(go.Bar(
        x=high_c,
        y=y_conj,
        orientation="h",
        name="Score ≥ 0.5 (conj)",
        marker_color="orange",
        width=0.35,
        hoverinfo="x+y"
    ))
    fig.add_trace(go.Bar(
        x=low_c,
        y=y_conj,
        base=high_c,
        orientation="h",
        name="Score < 0.5 (conj)",
        marker_color="blue",
        width=0.35,
        hoverinfo="x+y"
    ))
    fig.add_trace(go.Bar(
        x=bad_c,
        y=y_conj,
        base=[h + l for h, l in zip(high_c, low_c)],
        orientation="h",
        name="Incorrect (conj)",
        marker_color="red",
        width=0.35,
        hoverinfo="x+y"
    ))

    fig.add_trace(go.Bar(
        x=high_w,
        y=y_wm,
        orientation="h",
        name="Score ≥ 0.5 (WM)",
        marker_color="orange",
        opacity=0.5,
        width=0.35,
        hoverinfo="x+y"
    ))
    fig.add_trace(go.Bar(
        x=low_w,
        y=y_wm,
        base=high_w,
        orientation="h",
        name="Score < 0.5 (WM)",
        marker_color="blue",
        opacity=0.5,
        width=0.35,
        hoverinfo="x+y"
    ))
    fig.add_trace(go.Bar(
        x=bad_w,
        y=y_wm,
        base=[h + l for h, l in zip(high_w, low_w)],
        orientation="h",
        name="Incorrect (WM)",
        marker_color="red",
        opacity=0.5,
        width=0.35,
        hoverinfo="x+y"
    ))

    fig.update_layout(
        title="Evaluation Scores Grouped by Model (evalConj vs evalConj_WM)",
        barmode="stack",
        yaxis=dict(
            tickmode="array",
            tickvals=base_y,
            ticktext=sorted_models,
            title="Model Name",
            autorange="reversed"
        ),
        xaxis_title="Number of Conjectures",
        height=1000,
        legend_title="Score Category",
        margin=dict(l=220, r=40, t=60, b=60)
    )

    return fig





excel_path = "logsAgent/agentResultsV4_simEval.xlsx"
def load_excel_summary(model_folder):
    if not Path(excel_path).exists():
        return None, f"❌ Excel file not found: {excel_path}"
    
    try:
        # df = pd.read_excel(excel_path, sheet_name=None)  # Load all sheets
        df = pd.read_excel(excel_path, sheet_name=None, skiprows=0,header=None, dtype=str)
        return df, "✅ Excel data loaded!"
    except Exception as e:
        return None, f"❌ Failed to load Excel: {e}"

from dash import dash_table, html

def dataframe_to_dash_table(df, max_rows=49):
    # Make sure columns are strings
    df.columns = [str(col) if col is not None else "" for col in df.columns]
    # df.columns = ["" if str(col).startswith("Unnamed") else str(col) for col in df.columns]
    # df = pd.read_excel("agentResults.xlsx", sheet_name="agentResults")
    
    # Replace 'Unnamed: X' headers with empty strings
    df.columns = ["" if str(col).startswith("Unnamed") else str(col) for col in df.columns]

    try:
        return dash_table.DataTable(
            data=df.head(max_rows).to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '1000px'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '5px',
                'fontSize': 12,
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': 'lightgrey',
                'fontWeight': 'bold'
            },
            fixed_rows={'headers': True},
            page_size=max_rows
        )
    except Exception as e:
        return html.Div(f"⚠️ Error rendering table: {e}", style={"color": "red"})



# Load default model's data to populate initial values
default_model = available_models[0]
model_data_cache[default_model] = load_model_data(default_model)
default_data = model_data_cache[default_model]

initial_row_values = sorted(default_data["allMbsModelsDict"].keys())

initial_column_values = sorted({
    conj.get("evaluationMethod", "Unknown")
    for model in default_data["allMbsModelsDict"].values()
    for conj in model.get("conjectures", [])
    if conj.get("evaluationMethod", "Unknown") != "Unknown"
})


# === Assign IDs and add two-way conversion dicts ===
modelDescriptions = default_data.get("allMbsModelsDict", {})





app.layout = html.Div([
    html.H2("Overview and Summaries"),

    # ==== CONTROL PANEL ====
    html.Div([
        html.Div([
            html.Label("Select LLM model:"),
            dcc.Dropdown(
                id="model-selector",
                options=[{"label": name, "value": name} for name in available_models],
                value=available_models[0],
                clearable=False,
                style={"width": "100%"}
            ),

            html.Label("Select visualization:"),
            dcc.Dropdown(
                id="visualization-mode",
                options=[
                    {"label": "Heatmap", "value": "heatmap"},
                    {"label": "Stacked Score Comparison", "value": "stacked"},
                    {"label": "Grouped Scores by Model", "value": "grouped"}
                ],
                value="heatmap",
                clearable=False,
                style={"width": "100%"}
            ),

            html.Label("Score mode:"),
            dcc.Dropdown(
                id="score_mode",
                options=[
                    {"label": "original score value", "value": "raw"},
                    {"label": "relative goodness score", "value": "relative"},
                    {"label": "binary goodness score", "value": "relativeBinary"},
                    {"label": "binary goodness score (avg ≥ 0.5 → 1)", "value": "binaryAverages"},
                ],
                value="raw",
                clearable=False,
                style={"width": "100%"}
            ),

            html.Label("Include incorrect models?"),
            dcc.Checklist(
                id="include-incorrect-toggle",
                options=[{"label": "Yes", "value": "include"}],
                value=[],
                style={"marginBottom": "10px"}
            ),

            html.Label("Model label style:"),
            dcc.RadioItems(
                id="model-label-toggle",
                options=[
                    {"label": "Full Name (e.g., twoMassPointsWithSpring1)", "value": "full"},
                    {"label": "ID Format (e.g., 1-1)", "value": "id"}
                ],
                value="full",
                labelStyle={"display": "block"},
                style={"marginBottom": "20px"}
            ),            

            html.Button("📤 Export Core Heatmap (SVG)", id="export-svg-button", n_clicks=0),
            html.Div(id="export-status", style={"marginTop": "10px", "color": "green"})
            
            
        ], style={"flex": 1, "minWidth": "300px"}),

        html.Div([
            html.Label("Select Models to Display:"),
            dcc.Dropdown(
                id="row-selector",
                multi=True,
                placeholder="Select model rows...",
                value=initial_row_values,
                style={"width": "100%", "marginBottom": "20px"}
            ),

            html.Label("Select Evaluation Methods to Display:"),
            dcc.Dropdown(
                id="column-selector",
                multi=True,
                placeholder="Select evaluation methods...",
                value=initial_column_values,
                style={"width": "100%", "marginBottom": "20px"}
            ),
        
            html.Button("Select All Models", id="select-all-models-btn", n_clicks=0, style={"marginBottom": "10px"}),
            html.Button("Select All Methods", id="select-all-methods-btn", n_clicks=0, style={"marginBottom": "10px"}),
        
        ], style={"flex": 1, "minWidth": "300px"}),
    ], style={"display": "flex", "gap": "40px", "flexWrap": "wrap", "marginBottom": "30px"}),

    dcc.Store(id="persisted-row-selection"),
    dcc.Store(id="persisted-column-selection"),


    html.H3("Summary Table for All Models"),
    html.Div(id="summary-table", style={"marginBottom": "30px"}),

    # ==== MAIN VISUALIZATION ====
    html.Div(id="visualization-output"),

    # ==== SAVE/LOAD BUTTONS ====
    html.Div([
        html.Button("💾 Save all changes", id="save-button", n_clicks=0),
        html.Button("🔄 Load changes", id="load-button", n_clicks=0),
    ], style={"marginTop": "20px", "marginBottom": "10px", "display": "flex", "gap": "20px"}),

    html.Div(id="save-status", style={"color": "green"}),
    html.Div(id="update-status", style={"color": "green"}),
    html.Div(id="load-status", style={"color": "blue"}),

    # ==== SCORE EDIT ====
    html.Div([
        html.Div(id="edit-target", style={"marginTop": "20px", "fontWeight": "bold"}),
        dcc.Input(id="score-input", type="number", step=0.01, min=0, max=1, placeholder="Enter new score..."),
        html.Button("Update score", id="update-button", n_clicks=0),
        dcc.Store(id="clicked-cell"),
        dcc.Store(id="score-update-timestamp")
    ]),

    # ==== CONJECTURE DETAILS ====
    html.H3("Specific Model Output (click a cell to see full model output)"),
    html.Pre(id="click-status", style={"whiteSpace": "pre-wrap", "fontSize": "14px"}),

    html.Details([
        html.Summary("📄 Conjecture Details (click to expand)", style={
            "fontSize": "16px", 
            "fontWeight": "bold", 
            "cursor": "pointer", 
            "padding": "10px 0"
        }),
        html.Div(id="conjecture-sections", style={"marginTop": "10px"})
    ]),

    # ==== DEBUG OUTPUT ====
    html.Details([
        html.Summary("🐞 Debug Output from debug_EC.txt", style={
            "fontSize": "16px", 
            "fontWeight": "bold", 
            "cursor": "pointer", 
            "padding": "10px 0", 
            "color": "#d13"
        }),
        html.Pre(id="debug-output", style={
            "whiteSpace": "pre-wrap",
            "fontSize": "13px",
            "backgroundColor": "#f4f4f4",
            "padding": "10px",
            "border": "1px solid #ccc",
            "marginBottom": "20px"
        })
    ]),
   
    html.Details([
        html.Summary("📊 Agent Results from agentResults.xlsx", style={
            "fontSize": "16px",
            "fontWeight": "bold",
            "cursor": "pointer",
            "padding": "10px 0",
            "color": "#156"
        }),
        html.Pre(id="excel-preview", style={
            "whiteSpace": "pre-wrap",
            "fontSize": "13px",
            "backgroundColor": "#f9f9f9",
            "padding": "10px",
            "border": "1px solid #ccc",
            "marginBottom": "20px",
            "overflowX": "auto",
            "maxHeight": "800px"
        })
    ]),    
    
])




####actual NEEEW
@app.callback(
    Output("export-status", "children"),
    Input("export-svg-button", "n_clicks"),
    State("model-selector", "value"),
    State("score_mode", "value"),
    State("include-incorrect-toggle", "value"),
    State("column-selector", "value"),
    State("row-selector", "value"),
    State("model-label-toggle", "value"),
    prevent_initial_call=True
)
def handle_export_svg(n_clicks, model_name, score_mode, toggle_value, selected_columns, selected_rows, model_label_mode):
    import plotly.io as pio
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    includeIncorrectModels = "include" in toggle_value
    eval_mode = (
        "relativeGoodnessScore" if score_mode == "relative" else
        "relativeBinary" if score_mode == "relativeBinary" else
        "binaryAverages" if score_mode == "binaryAverages" else
        "raw"
    )

    try:
        if model_name not in model_data_cache:
            model_data_cache[model_name] = load_model_data(model_name)
        data = model_data_cache[model_name]

        figure, df_numeric, label_df, df_numeric2, label_df2 = build_model_method_score_heatmap_plotly(
            data,
            evalMethod=eval_mode,
            includeIncorrectModels=includeIncorrectModels,
            visible_columns=selected_columns,
            visible_rows=selected_rows,
            highlighted_cell=None,
            model_label_mode=model_label_mode
        )

        # STEP 1: Get original core columns (before renaming)
        core_cols_orig = [col for col in df_numeric.columns if col not in ["Sum", "Average", "Avg+Rule", "ProductScore", "Incorrect Count"]]
        core_rows_orig = [idx for idx in df_numeric.index if idx not in ["Sum", "Average"]]
        core_rows = core_rows_orig  # always slice using original names



        #this works ############################################
        # STEP 2: Rename only core columns if in 'id' mode
        if model_label_mode == "id":
            # method_rename_map = {name: f"{evalMethod2ID.get(name, '?')} - {name}" for name in core_cols_orig}
            method_rename_map = {name: f"{evalMethod2ID.get(name, '?')}" for name in core_cols_orig}
            df_numeric = df_numeric.rename(columns=method_rename_map)
            df_numeric2 = df_numeric2.rename(columns=method_rename_map)
            core_cols = list(method_rename_map.values())
            
        else:
            core_cols = core_cols_orig
        #this works############################################

        z_vals_1 = df_numeric.loc[core_rows, core_cols].fillna(0).astype(float)
        z_vals_2 = df_numeric2.loc[core_rows, core_cols].fillna(0).astype(float)        

        y_vals = z_vals_1.index.tolist()
        
        # Then map display labels if needed
        if model_label_mode == "id":
            y_vals_display = [modelName2mbsID.get(m, m) for m in y_vals]
        else:
            y_vals_display = y_vals


        # Group rows by their main ID (before the '-')
        group_rows = defaultdict(list)
        for idx, label in enumerate(y_vals_display):
            group_id = label.split('-')[0]
            group_rows[group_id].append(idx)


        # Step 4: Column labels
        core_cols_display = z_vals_1.columns.tolist()

        
        # Replace "N.N." with np.nan BEFORE converting to float
        df_numeric.replace("N.N.", np.nan, inplace=True)
        df_numeric2.replace("N.N.", np.nan, inplace=True)
        
        z_vals_1 = df_numeric.loc[core_rows, core_cols].astype(float)
        z_vals_2 = df_numeric2.loc[core_rows, core_cols].astype(float)

        custom_colorscale = [
            [0.0, "#ff8080"],     # red at 0
            [0.5, "#4040D0"],    # mid
            [1.0, "#002080"]     # dark blue for 1
        ]
        
        cell_width = 35
        cell_height = 35/2
        fontSize=30
        
        fig = make_subplots(
            rows=1, cols=2,
            shared_yaxes=True,
            subplot_titles=("(correct) models", "intentionally incorrect models"),
            horizontal_spacing=0.025, ####<-- change here for title spae
        )
        

        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(size=fontSize, color="black")
                
        fig.add_trace(go.Heatmap(
            z=z_vals_1.values,
            x=core_cols_display,
            y=y_vals,
            colorscale=custom_colorscale,
            zmin=0, zmax=1,
            zauto=False,
            showscale=False,
            hoverinfo="skip",
            xgap=0,
            ygap=0,
            connectgaps=False,  # ✅ Ensures NaNs are rendered as transparent
        ), row=1, col=1)
        
        fig.add_trace(go.Heatmap(
            z=z_vals_2.values,
            x=core_cols_display,
            y=y_vals,
            colorscale=custom_colorscale,
            colorbar=dict(len=1.0, y=0.5, tickfont=dict(size=fontSize)),
            zmin=0, zmax=1,
            zauto=False,
            showscale=True,
            hoverinfo="skip",
            xgap=0,
            ygap=0,
            connectgaps=False,
        ), row=1, col=2)
               
        # Cell borders (shapes)
        shapes = []
        for subplot_idx in [1, 2]:
            for i, y_label in enumerate(y_vals_display):
                for j, x_label in enumerate(core_cols_display):
                    shapes.append(dict(
                        type="rect",
                        xref=f"x{subplot_idx}",
                        yref=f"y{subplot_idx}",
                        x0=j - 0.5,
                        x1=j + 0.5,
                        y0=i - 0.5,
                        y1=i + 0.5,
                        line=dict(color="black", width=0.5),
                        fillcolor="rgba(0,0,0,0)"
                    ))
        
        # Get number of rows and columns
        n_rows = len(y_vals_display)
        n_cols = len(core_cols_display)
        
        # Box around subplot 1 (left heatmap)
        shapes.append(dict(
            type="rect",
            xref="x1",
            yref="y1",
            x0=-0.5,
            x1=n_cols - 0.5,
            y0=-0.5,
            y1=n_rows - 0.5,
            line=dict(color="black", width=2),  # <--- THICK border
            fillcolor="rgba(0,0,0,0)"
        ))
        
        # Box around subplot 2 (right heatmap)
        shapes.append(dict(
            type="rect",
            xref="x2",
            yref="y2",
            x0=-0.5,
            x1=n_cols - 0.5,
            y0=-0.5,
            y1=n_rows - 0.5,
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)"
        ))
        
        # Add thick horizontal divider lines every 2 rows
        for r in range(2, len(y_vals_display), 2):
            # Left subplot
            shapes.append(dict(
                type="line",
                xref="x1", yref="y1",
                x0=-0.5, x1=n_cols - 0.5,
                y0=r - 0.5, y1=r - 0.5,
                line=dict(color="black", width=2),
            ))
            # Right subplot
            shapes.append(dict(
                type="line",
                xref="x2", yref="y2",
                x0=-0.5, x1=n_cols - 0.5,
                y0=r - 0.5, y1=r - 0.5,
                line=dict(color="black", width=2),
            ))     
          
        fig.update_layout(shapes=shapes)
        
        # Single, explicit layout update
        fig.update_layout(
            width=2 * cell_width * len(core_cols_display),
            height=cell_height * len(y_vals_display),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=30, r=30, t=60, b=80),####<-- change here for margin
            font=dict(size=fontSize, color="black"),
        )
        fig.update_xaxes(automargin=True)
        fig.update_yaxes(automargin=True)

        fig.update_yaxes(
            tickvals=[],
            ticktext=[],
            autorange=True,
            ticklen=2,
            title=dict(
                text="mechanical model k",
                font=dict(size=fontSize, color="black"), 
                standoff=60  # ####<-- change here for y-title further away from the axis
            ),
            automargin=True,
            tickfont=dict(size=fontSize),
            row=1, col=1
        )
        
        fig.update_xaxes(
            tickvals=[],
            ticktext=[],
            autorange=True,
            ticklen=0,
            automargin=True,
            tickfont=dict(size=fontSize),
            row=1, col=1
        )
        fig.update_xaxes(
            tickvals=[],
            ticktext=[],
            autorange=True,
            ticklen=0,
            automargin=True,
            tickfont=dict(size=fontSize),
            row=1, col=2
        )


        # Add manual x-tick labels to both subplots (e.g. 1, 5, 9, 13, 17)
        x_indices_to_show = list(range(0, len(core_cols_display), 4))  # every 4th column
        
        for idx, (group_id, row_indices) in enumerate(group_rows.items()):
            if idx % 2 != 0:
                continue  # ❌ skip all but every 3rd group
        
            center_row = (min(row_indices) + max(row_indices)) / 2
            fig.add_annotation(
                text=group_id,
                xref="paper",
                yref="y1",
                x=-0.006,
                y=center_row,
                showarrow=False,
                font=dict(size=fontSize, color="black"),
                align="right",
                xanchor="right",
            )


        n_labels = 7                             # how many labels you want (1 and 18 included)      
        # Compute indices evenly spaced between 0 and n_cols - 1
        x_indices_to_show = np.linspace(0, n_cols - 1, n_labels, dtype=int).tolist()
        
        for subplot_idx in [1, 2]:
            for j in x_indices_to_show:
                col_label = str(core_cols_display[j])
                fig.add_annotation(
                    text=col_label,
                    x=j,
                    y=0.0,  # ⬅️ adjust spacing from plot
                    xref=f"x{subplot_idx}",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=fontSize, color="black"),
                    xanchor="center",
                    yanchor="top"
                )
        
        if model_label_mode == "id":
            tickangle=0
        else:
            tickangle=45
        
          # ✅ Add shared x-axis label across both subplots
        fig.add_annotation(
            text="evaluation methods",
            xref="paper", yref="paper",
            x=0.5, y=-0.07,  # ####<-- xchange here for y-lables further left
            showarrow=False,
            font=dict(size=fontSize, color="black"),
        )

        # Decide on suffix for filename
        suffix = "id" if model_label_mode == "id" else "name"
        
        # Construct the new output path
        figures_folder = Path(base_folder) / "figures"
        figures_folder.mkdir(parents=True, exist_ok=True)  # Ensure folder exists
        
        # Build filenames
        filename_svg = f"{model_name}_HeatMap_{suffix}.svg"
        filename_png = f"{model_name}_HeatMap_{suffix}.png"
        
        # Full paths
        output_path = figures_folder / filename_svg
        output_path2 = figures_folder / filename_png
        
        # Export
        # pio.write_image(fig, str(output_path), format="svg", engine="orca")
        pio.write_image(fig, str(output_path2), format="png", scale=4, engine="orca")


        return f"✅ Exported SVG to: {output_path}"

    except Exception as e:
        return f"❌ Export failed: {e}"

# ####actual NEEEW
# @app.callback(
#     Output("export-status", "children"),
#     Input("export-svg-button", "n_clicks"),
#     State("model-selector", "value"),
#     State("score_mode", "value"),
#     State("include-incorrect-toggle", "value"),
#     State("column-selector", "value"),
#     State("row-selector", "value"),
#     State("model-label-toggle", "value"),
#     prevent_initial_call=True
# )
# def handle_export_svg(n_clicks, model_name, score_mode, toggle_value, selected_columns, selected_rows, model_label_mode):
#     import plotly.io as pio
#     import plotly.graph_objects as go
#     from plotly.subplots import make_subplots

#     includeIncorrectModels = "include" in toggle_value
#     eval_mode = (
#         "relativeGoodnessScore" if score_mode == "relative" else
#         "relativeBinary" if score_mode == "relativeBinary" else
#         "binaryAverages" if score_mode == "binaryAverages" else
#         "raw"
#     )

#     try:
#         if model_name not in model_data_cache:
#             model_data_cache[model_name] = load_model_data(model_name)
#         data = model_data_cache[model_name]

#         figure, df_numeric, label_df, df_numeric2, label_df2 = build_model_method_score_heatmap_plotly(
#             data,
#             evalMethod=eval_mode,
#             includeIncorrectModels=includeIncorrectModels,
#             visible_columns=selected_columns,
#             visible_rows=selected_rows,
#             highlighted_cell=None,
#             model_label_mode=model_label_mode
#         )

#         # STEP 1: Get original core columns (before renaming)
#         core_cols_orig = [col for col in df_numeric.columns if col not in ["Sum", "Average", "Avg+Rule", "ProductScore", "Incorrect Count"]]
#         core_rows_orig = [idx for idx in df_numeric.index if idx not in ["Sum", "Average"]]
#         core_rows = core_rows_orig  # always slice using original names



#         #this works ############################################
#         # STEP 2: Rename only core columns if in 'id' mode
#         if model_label_mode == "id":
#             # method_rename_map = {name: f"{evalMethod2ID.get(name, '?')} - {name}" for name in core_cols_orig}
#             method_rename_map = {name: f"{evalMethod2ID.get(name, '?')}" for name in core_cols_orig}
#             df_numeric = df_numeric.rename(columns=method_rename_map)
#             df_numeric2 = df_numeric2.rename(columns=method_rename_map)
#             core_cols = list(method_rename_map.values())
            
#         else:
#             core_cols = core_cols_orig
#         #this works############################################

#         z_vals_1 = df_numeric.loc[core_rows, core_cols].fillna(0).astype(float)
#         z_vals_2 = df_numeric2.loc[core_rows, core_cols].fillna(0).astype(float)        

#         y_vals = z_vals_1.index.tolist()
        
#         # Then map display labels if needed
#         if model_label_mode == "id":
#             y_vals_display = [modelName2mbsID.get(m, m) for m in y_vals]
#         else:
#             y_vals_display = y_vals

#         # Step 4: Column labels
#         core_cols_display = z_vals_1.columns.tolist()

        
#         # Replace "N.N." with np.nan BEFORE converting to float
#         df_numeric.replace("N.N.", np.nan, inplace=True)
#         df_numeric2.replace("N.N.", np.nan, inplace=True)
        
#         z_vals_1 = df_numeric.loc[core_rows, core_cols].astype(float)
#         z_vals_2 = df_numeric2.loc[core_rows, core_cols].astype(float)

#         custom_colorscale = [
#             [0.0, "#ff8080"],     # red at 0
#             [0.5, "#4040D0"],    # mid
#             [1.0, "#002080"]     # dark blue for 1
#         ]
        
#         cell_width = 35
#         cell_height = 35
#         fontSize=20
        
#         fig = make_subplots(
#             rows=1, cols=2,
#             shared_yaxes=True,
#             subplot_titles=("evalConj", "evalConj_WM"),
#             horizontal_spacing=0.02,
#         )
        

#         for annotation in fig['layout']['annotations']:
#             annotation['font'] = dict(size=fontSize)
                
#         fig.add_trace(go.Heatmap(
#             z=z_vals_1.values,
#             x=core_cols_display,
#             y=y_vals,
#             colorscale=custom_colorscale,
#             zmin=0, zmax=1,
#             zauto=False,
#             showscale=False,
#             hoverinfo="skip",
#             xgap=0,
#             ygap=0,
#             connectgaps=False,  # ✅ Ensures NaNs are rendered as transparent
#         ), row=1, col=1)
        
#         fig.add_trace(go.Heatmap(
#             z=z_vals_2.values,
#             x=core_cols_display,
#             y=y_vals,
#             colorscale=custom_colorscale,
#             colorbar=dict(len=1.0, y=0.5, tickfont=dict(size=fontSize)),
#             zmin=0, zmax=1,
#             zauto=False,
#             showscale=True,
#             hoverinfo="skip",
#             xgap=0,
#             ygap=0,
#             connectgaps=False,
#         ), row=1, col=2)
               
#         # Cell borders (shapes)
#         shapes = []
#         for subplot_idx in [1, 2]:
#             for i, y_label in enumerate(y_vals_display):
#                 for j, x_label in enumerate(core_cols_display):
#                     shapes.append(dict(
#                         type="rect",
#                         xref=f"x{subplot_idx}",
#                         yref=f"y{subplot_idx}",
#                         x0=j - 0.5,
#                         x1=j + 0.5,
#                         y0=i - 0.5,
#                         y1=i + 0.5,
#                         line=dict(color="black", width=1),
#                         fillcolor="rgba(0,0,0,0)"
#                     ))
#         fig.update_layout(shapes=shapes)
        
#         # Single, explicit layout update
#         fig.update_layout(
#             width=2 * cell_width * len(core_cols_display),
#             height=cell_height * len(y_vals_display),
#             plot_bgcolor="white",
#             paper_bgcolor="white",
#             margin=dict(l=120, r=120, t=60, b=140),
#             font=dict(size=fontSize),
#         )

        
#         fig.update_yaxes(
#             tickmode="array",
#             tickvals=y_vals,           # <- The actual values used for plotting
#             ticktext=y_vals_display,   # <- The labels you want to display (IDs)
#             # autorange="reversed",
#             autorange=True,
#             title=dict(text="models", font=dict(size=fontSize)),
#             automargin=True,
#             tickfont=dict(size=fontSize),
#             row=1, col=1  # optional if using `make_subplots`
#         )
        
#         if model_label_mode == "id":
#             tickangle=0
#         else:
#             tickangle=45
            
#         fig.update_xaxes(
#             tickangle=tickangle,
#             automargin=True,
#             # title="evaluation methods",
#             tickfont=dict(size=fontSize),  
#             row=1, col=1
#         )       
#         fig.update_xaxes(
#             tickangle=tickangle,
#             automargin=True,
#             # title="evaluation methods",
#             tickfont=dict(size=fontSize), 
#             row=1, col=2
#         )

#         fig.update_yaxes(
#             row=1, col=2,  # or col=2 for the second plot
#             tickmode="array",
#             tickvals=list(range(len(z_vals_1.index))),
#             ticktext=z_vals_1.index.tolist(),
#             # autorange="reversed",
#             autorange=True,
#             # title="models",
#             automargin=True,
#             tickfont=dict(size=fontSize),
#         )
        
#           # ✅ Add shared x-axis label across both subplots
#         fig.add_annotation(
#             text="evaluation methods",
#             xref="paper", yref="paper",
#             x=0.5, y=-0.03,  # move slightly up
#             showarrow=False,
#             font=dict(size=fontSize),
#         )

#         # Decide on suffix for filename
#         suffix = "id" if model_label_mode == "id" else "name"
        
#         # Construct the new output path
#         figures_folder = Path(base_folder) / "figures"
#         figures_folder.mkdir(parents=True, exist_ok=True)  # Ensure folder exists
        
#         # Build filenames
#         filename_svg = f"{model_name}_HeatMap_{suffix}.svg"
#         filename_png = f"{model_name}_HeatMap_{suffix}.png"
        
#         # Full paths
#         output_path = figures_folder / filename_svg
#         output_path2 = figures_folder / filename_png
        
#         # Export
#         pio.write_image(fig, str(output_path), format="svg", engine="orca")
#         pio.write_image(fig, str(output_path2), format="png", scale=4, engine="orca")


#         return f"✅ Exported SVG to: {output_path}"

#     except Exception as e:
#         return f"❌ Export failed: {e}"





def compute_summary_metrics_all_models(eval_mode="raw", includeIncorrectModels=False, visible_rows=None, visible_columns=None, model_label_mode="full"):
    rows = []
    for model_name in available_models:
        try:
            data = model_data_cache.get(model_name)
            if data is None:
                data = load_model_data(model_name)
                model_data_cache[model_name] = data

            # Generate heatmap figure
            fig, df_numeric1, label_df1, df_numeric2, label_df2 = build_model_method_score_heatmap_plotly(
                data,
                evalMethod=eval_mode,
                includeIncorrectModels=includeIncorrectModels,
                visible_columns=visible_columns,
                visible_rows=visible_rows,
                highlighted_cell=None,
                model_label_mode="full"
            )

            def compute_thresholded_avg_core_rows(heatmap_data):
                if hasattr(heatmap_data, 'z') and hasattr(heatmap_data, 'y'):
                    df = pd.DataFrame(heatmap_data.z, index=heatmap_data.y, columns=heatmap_data.x)
            
                    # Exclude rows like 'Sum', 'Average', etc.
                    core_rows = [row for row in df.index if row.lower() not in ("sum", "average")]
                    core_df = df.loc[core_rows]
            
                    # Flatten to a 1D array, drop NaNs
                    flat_values = core_df.values.flatten()
                    valid_values = flat_values[np.isfinite(flat_values)]
            
                    if valid_values.size == 0:
                        return np.nan
            
                    thresholded = (valid_values >= 0.75).astype(float)
                    return thresholded.mean()
                return np.nan


            
            threshold_avg_A = compute_thresholded_avg_core_rows(fig.data[0])
            
            threshold_avg_B = (
                compute_thresholded_avg_core_rows(fig.data[1])
                if len(fig.data) > 1 else np.nan
            )

            # Extract standard summary metrics from annotation
            summary_text = fig.layout.annotations[0]['text']
            values = {
                "Model": model_name,
                "Average (evalConj)": None,
                "Avg+Rule (evalConj)": None,
                "ProductScore (evalConj)": None,
                "Average (evalConj_WM)": None,
                "Avg+Rule (evalConj_WM)": None,
                "ProductScore (evalConj_WM)": None,
                "≥0.75 Threshold Avg (evalConj)": threshold_avg_A,
                "≥0.75 Threshold Avg (evalConj_WM)": threshold_avg_B,
            }

            pattern = r"Average \(mean of rows\): ([0-9.]+).*?Avg\+Rule: ([0-9.]+).*?Product Score: ([0-9.]+)"
            matches = re.findall(pattern, summary_text)

            if len(matches) >= 2:
                values["Average (evalConj)"] = float(matches[0][0])
                values["Avg+Rule (evalConj)"] = float(matches[0][1])
                values["ProductScore (evalConj)"] = float(matches[0][2])
                values["Average (evalConj_WM)"] = float(matches[1][0])
                values["Avg+Rule (evalConj_WM)"] = float(matches[1][1])
                values["ProductScore (evalConj_WM)"] = float(matches[1][2])

            rows.append(values)

        except Exception as e:
            rows.append({"Model": model_name, "Error": str(e)})

    # Convert to DataFrame and round numeric columns
    df = pd.DataFrame(rows)
    for col in df.select_dtypes(include=["float", "int"]).columns:
        df[col] = df[col].round(3)
        
    # Apply label shortening if requested
    if model_label_mode == "id":
        df["Model"] = df["Model"].apply(
            lambda m: f"{modelName2mbsID.get(m, '?')}-{''.join(filter(str.isdigit, m.split('_')[-1])) or '?'}"
        )        

    return df


@app.callback(
    Output("summary-table", "children"),
    Input("score_mode", "value"),
    Input("include-incorrect-toggle", "value"),
    Input("row-selector", "value"),
    Input("column-selector", "value"),
    Input("model-label-toggle", "value"),
)
def update_summary_table(score_mode, toggle_value, selected_rows, selected_columns, model_label_mode):
    includeIncorrectModels = "include" in toggle_value
    eval_mode = (
        "relativeGoodnessScore" if score_mode == "relative" else
        "relativeBinary" if score_mode == "relativeBinary" else
        "binaryAverages" if score_mode == "binaryAverages" else
        "raw"
    )
    df = compute_summary_metrics_all_models(
        eval_mode=eval_mode,
        includeIncorrectModels=includeIncorrectModels,
        visible_rows=selected_rows,
        visible_columns=selected_columns,
        model_label_mode="full"  # 👈 Force full label for summary
    )
    return dataframe_to_dash_table(df)






@app.callback(
    Output("row-selector", "options"),
    Input("model-selector", "value"),
)
def update_row_selector(model_name):
    if model_name not in model_data_cache:
        model_data_cache[model_name] = load_model_data(model_name)
    data = model_data_cache[model_name]

    models = sorted(data.get("allMbsModelsDict", {}).keys())
    options = [{"label": m, "value": m} for m in models]

    return options

@app.callback(
    Output("column-selector", "options"),
    Input("model-selector", "value"),
)
def update_column_selector(model_name):
    if model_name not in model_data_cache:
        model_data_cache[model_name] = load_model_data(model_name)
    data = model_data_cache[model_name]

    methods = sorted({
        conj.get("evaluationMethod", "Unknown")
        for model_data in data.get("allMbsModelsDict", {}).values()
        for conj in model_data.get("conjectures", [])
        if conj.get("evaluationMethod", "Unknown") != "Unknown"
    })

    options = [{"label": m, "value": m} for m in methods]
    return options

@app.callback(
    Output("row-selector", "value"),
    Input("select-all-models-btn", "n_clicks"),
    State("row-selector", "options"),
    prevent_initial_call=True
)
def select_all_models(n, options):
    return [opt["value"] for opt in options]

@app.callback(
    Output("column-selector", "value"),
    Input("select-all-methods-btn", "n_clicks"),
    State("column-selector", "options"),
    prevent_initial_call=True
)
def select_all_methods(n, options):
    return [opt["value"] for opt in options]

@app.callback(
    Output("visualization-output", "children"),
    Input("visualization-mode", "value"),
    Input("model-selector", "value"),
    Input("score_mode", "value"),
    Input("include-incorrect-toggle", "value"),
    Input("column-selector", "value"),
    Input("score-update-timestamp", "data"),
    Input("row-selector", "value"),
    Input("clicked-cell", "data"),
    Input("model-label-toggle", "value"),
)
def update_visualization(mode, selected_model, score_mode, toggle_value, 
                         selected_columns=None, _update_timestamp=None, 
                         selected_rows=None, clicked_cell=None, model_label_mode="full"):
    includeIncorrectModels = "include" in toggle_value

    if selected_model not in model_data_cache:
        model_data_cache[selected_model] = load_model_data(selected_model)
    data = model_data_cache[selected_model]

    # Determine score mode
    eval_mode = (
        "relativeGoodnessScore" if score_mode == "relative" else
        "relativeBinary" if score_mode == "relativeBinary" else
        "binaryAverages" if score_mode == "binaryAverages" else
        "raw"
    )

    if mode == "heatmap":
        figure, df_numeric1, label_df1, df_numeric2, label_df2 = build_model_method_score_heatmap_plotly(
            data, 
            evalMethod=eval_mode, 
            includeIncorrectModels=includeIncorrectModels, 
            visible_columns=selected_columns,
            visible_rows=selected_rows,
            highlighted_cell=clicked_cell,
            model_label_mode=model_label_mode
        )
        
        return dcc.Graph(
            id="heatmap",
            figure=figure
        )
    elif mode == "stacked":
        return dcc.Graph(
            id="stacked-plot",
            figure=build_horizontal_stacked_score_comparison_plot(data)
        )
    elif mode == "grouped":
        return dcc.Graph(
            id="grouped-model-plot",
            figure=plot_scores_grouped_by_model_name_with_wm_plotly(data)
        )
    else:
        return html.Div("⚠️ Unknown visualization mode.")
    
@app.callback(
    Output("stacked-comparison", "figure"),
    Input("model-selector", "value")
)
def update_stacked_comparison_plot(selected_model):
    if selected_model not in model_data_cache:
        model_data_cache[selected_model] = load_model_data(selected_model)
    data = model_data_cache[selected_model]
    return build_horizontal_stacked_score_comparison_plot(data)
@app.callback(
    Output("grouped-model-plot", "figure"),
    Input("model-selector", "value")
)
def update_grouped_model_plot(selected_model):
    if selected_model not in model_data_cache:
        model_data_cache[selected_model] = load_model_data(selected_model)
    data = model_data_cache[selected_model]
    return plot_scores_grouped_by_model_name_with_wm_plotly(data)

@app.callback(
    Output("load-status", "children"),
    Input("load-button", "n_clicks"),
    State("model-selector", "value")
)
def handle_load(n_clicks, model_choice):
    if not n_clicks or not model_choice:
        raise PreventUpdate
    try:
        save_path = Path(base_folder) / model_choice / "output" / "figures" / "updated_data.json"
        with open(save_path, "r", encoding="utf-8") as f:
            model_data_cache[model_choice] = json.load(f)
        return "✅ Data loaded!"
    except Exception as e:
        return f"❌ Load error: {e}"


@app.callback(
    Output("save-status", "children"),
    Input("save-button", "n_clicks"),
    State("model-selector", "value")
)
def handle_save(n_clicks, model_choice):
    if not n_clicks or not model_choice:
        raise PreventUpdate
    try:
        save_path = Path(base_folder) / model_choice / "output" / "figures" / "updated_data.json"
        os.makedirs(save_path.parent, exist_ok=True)
        data = model_data_cache.get(model_choice)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return "✅ Data saved!"
    except Exception as e:
        return f"❌ Save failed: {e}"


@app.callback(
    Output("update-status", "children"),
    Output("score-update-timestamp", "data"),
    Input("update-button", "n_clicks"),
    State("model-selector", "value"),
    State("score-input", "value"),
    State("clicked-cell", "data")
)
def handle_score_update(n_clicks, model_choice, new_score, clicked_info):
    if not n_clicks or not model_choice or new_score is None or not clicked_info:
        raise PreventUpdate
    try:
        model = clicked_info["model"]
        method = clicked_info["method"]
        source = clicked_info["source"]
        data = model_data_cache[model_choice]
        models = data[source]["allModelsResultsDicts"]
        conj_list = data["allMbsModelsDict"][model]["conjectures"]
        for i, conj in enumerate(conj_list):
            if conj.get("evaluationMethod") == method:
                models[model]["conjecturesEvaluated"][i]["scoreValue"] = float(new_score)
                break
        # ✅ Update timestamp to trigger visualization callback
        return "✅ Score updated!", time()
    except Exception as e:
        return f"❌ Update error: {e}", None


@app.callback(
    [Output("edit-target", "children"),
     Output("score-input", "value"),
     Output("clicked-cell", "data")],
    Input("heatmap", "clickData"),
    State("model-selector", "value")  # <-- add model selection
)
def on_click(cell, selected_model):
    if not cell or "points" not in cell or not selected_model:
        raise PreventUpdate

    try:
        model, method, source, model_cx = cell["points"][0]["customdata"].split("|")
    except Exception:
        return "⚠️ Could not parse clicked cell.", None, None

    try:
        path = f"{base_folder}/{selected_model}/results.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        models = data[source]["allModelsResultsDicts"]
        conj_list = data["allMbsModelsDict"][model]["conjectures"]
        for i, conj in enumerate(conj_list):
            if conj["evaluationMethod"] == method:
                score = models[model]["conjecturesEvaluated"][i]["scoreValue"]
                break
        else:
            score = None

    except Exception:
        score = None

    label_html = f"Editing score for model '{model}' and method '{method}' in {source}"
    return label_html, score, {"model": model, "method": method, "source": source}



@app.callback(
    Output("conjecture-sections", "children"),
    Output("click-status", "children"),
    Output("debug-output", "children"),
    Input("clicked-cell", "data"),
    Input("model-selector", "value"),
    Input("visualization-mode", "value"),
)
def update_conjecture_display(clicked_info, selected_model, vis_mode):
    if vis_mode != "heatmap" or not clicked_info:
        return [], "", ""

    try:
        path = f"{base_folder}/{selected_model}/results.json"
        with open(path, "r", encoding="utf-8") as f:
            current_data = json.load(f)

        model = clicked_info["model"]
        method = clicked_info["method"]
        source = clicked_info["source"]

        conj_list = current_data["allMbsModelsDict"].get(model, {}).get("conjectures", [])
        conj_id = None
        conj_idx = None
        for i, conj in enumerate(conj_list):
            if conj.get("evaluationMethod") == method:
                conj_id = current_data[source]["allModelsResultsDicts"][model]["conjecturesEvaluated"][i].get("currentMBSmodelNameIDcID", "")
                conj_idx = i
                break

        if conj_id is None or conj_idx is None:
            return [html.Div("⚠️ No matching conjecture found.")], f"No output for model: {selected_model}", ""

        model_cx = conj_id
        sections = get_conjecture_sections(current_data, model_cx, source)

        if re.match(r".+c\d+$", model_cx) and "_c" not in model_cx:
            model_cx = re.sub(r"c(\d+)$", r"_c\1", model_cx)

        # === Debug log extraction for BOTH evalConj and evalConj_WM ===
        debug_file_path = Path(base_folder) / selected_model / "debug_EC.txt"
        debug_text_evalConj = "⚠️ Debug log not found."
        debug_text_evalConjWM = "⚠️ Debug log not found."
        
        model_base = model_cx.split("_c")[0]
        match = re.search(r'c(\d+)$', model_cx)
        if not match:
            return [], f"⚠️ Invalid model_cx format: {model_cx}", ""
        conj_num = int(match.group(1))

        if debug_file_path.exists():
            with open(debug_file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for src_key, target_var in [("evalConj", "debug_text_evalConj"), ("evalConj_WM", "debug_text_evalConjWM")]:
                block_index = 0 if src_key == "evalConj" else 1
                start_blocks = [
                    i for i, line in enumerate(lines)
                    if line.strip() == f"Evaluate conjecture {conj_num} of model {model_base}"
                ]
                if len(start_blocks) > block_index:
                    start_index = start_blocks[block_index]
                    raw_end_index = next(
                        (
                            i for i in range(start_index + 1, len(lines))
                            if re.match(r"Evaluate conjecture \d+ of model .+", lines[i].strip())
                        ),
                        None
                    )
                    end_index = raw_end_index - 1 if raw_end_index is not None else len(lines)
                    block_lines = lines[start_index:end_index]
                    extracted_text = "".join(block_lines).strip()
                else:
                    extracted_text = f"⚠️ Could not find debug block for {model_base} c{conj_num} ({src_key})"

                if src_key == "evalConj":
                    debug_text_evalConj = extracted_text
                else:
                    debug_text_evalConjWM = extracted_text

        debug_text_combined = (
            f"\n╔══════════════════════════════════════╗\n"
            f"║ 🟠 DEBUG OUTPUT: evalConj_WM        ║\n"
            f"╚══════════════════════════════════════╝\n"
            f"{debug_text_evalConjWM}\n\n"
            f"╔══════════════════════════════════╗\n"
            f"║ 🔵 DEBUG OUTPUT: evalConj       ║\n"
            f"╚══════════════════════════════════╝\n"
            f"{debug_text_evalConj}"
            if source == "evalConj_WM"
            else
            f"\n╔══════════════════════════════════╗\n"
            f"║ 🔵 DEBUG OUTPUT: evalConj        ║\n"
            f"╚══════════════════════════════════╝\n"
            f"{debug_text_evalConj}\n\n"
            f"╔══════════════════════════════════════╗\n"
            f"║ 🟠 DEBUG OUTPUT: evalConj_WM         ║\n"
            f"╚══════════════════════════════════════╝\n"
            f"{debug_text_evalConjWM}"
        )


        # === Conjecture info blocks ===
        content_blocks = []
        for title, text in sections.items():
            content_blocks.append(html.Div([
                html.H4(title),
                html.Pre(text, style={
                    "whiteSpace": "pre-wrap",
                    "fontSize": "13px",
                    "maxHeight": "300px",
                    "overflowY": "auto",
                    "border": "1px solid #ccc",
                    "padding": "10px",
                    "backgroundColor": "#f9f9f9",
                    "marginBottom": "20px"
                })
            ]))

        return content_blocks, f"📄 Showing conjecture: {selected_model}/results.json: {model_cx} ({source})", debug_text_combined

    except Exception as e:
        return [html.Div(f"❌ Error loading conjecture: {e}")], "⚠️ Could not load conjecture", ""



@app.callback(
    Output("excel-preview", "children"),
    Input("model-selector", "value")
)
def update_excel_table(selected_model):
    df_sheets, status = load_excel_summary(selected_model)
    if df_sheets is None:
        return html.Div(status, style={"color": "red"})

    df = df_sheets["agentResults"]
    return dataframe_to_dash_table(df, max_rows=49)





# === RUN SERVER ===
if __name__ == "__main__":
    import plotly.io as pio
    import threading
    import webbrowser

    pio.renderers.default = "browser"
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:8050")).start()
    app.run(debug=True)