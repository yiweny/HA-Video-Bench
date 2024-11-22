# HA-Video-Bench
The repository contains the source code for **HA-Video-Bench**. To reproduce the results, you need to download necessary dependencies. 

# Evaluation Scripts
The following table contains the code path to produce evaluations under each dimension.
| Dimension  |  Code Path |
|---|---|
| Image Quality  |  `python3 few_shot/fewscore_staticquality.py --dimension imaging_quality` |
| Aesthetic Quality  | `python3 few_shot/fewscore_staticquality.py --dimension aesthetic_quality`  |
| Temporal Consistency | `python3 few_shot/fewshot_dynamicquality.py --dimension temporal_consistency`  |
| Motion Effects | `python3 few_shot/fewshot_dynamicquality.py --dimension motion_effects` |
| Object-Class Consistency | `python3 chain_of_query/prompt/object_class.py` |
| Video-Text Consistency | `python3 chain_of_query/prompt/overall_consistency.py` |
| Color Consistency | `python3 chain_of_query/prompt/color.py` |
| Action Consistency | `python3 chain_of_query/prompt/action.py` |
| Scene Consistency |`python3 chain_of_query/prompt/scene.py` |
