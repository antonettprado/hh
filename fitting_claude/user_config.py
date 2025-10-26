"""
USER CONFIGURATION FILE

This is the ONLY file you need to edit to change selections and era combinations.
All other modules will automatically use these settings.

To modify the analysis:
1. Edit the SELECTIONS and ERAS_TO_COMBINE dictionaries below
2. Save this file
3. Run your analysis - the new settings will be used automatically

No need to edit any other files!
"""

# ==============================================================================
# SELECTION COMBINATIONS
# ==============================================================================
# Define which channels should be combined into named selections
# 
# Format:
#   'selection_name': ['channel1', 'channel2', ...]
#
# These selections will be used to create combined datacards

SELECTIONS = {
    '3j_4j': [
        'SL_3j_resolved',
        'SL_4j_resolved'
    ],
    
    '3j1b_3j2b_4j1b_4j2b': [
        'SL_res_3j_1b',
        'SL_res_3j_2b',
        'SL_res_4j_1b',
        'SL_res_4j_2b'
    ],
}


# ==============================================================================
# ERA COMBINATIONS
# ==============================================================================
# Define which eras should be combined into named periods
#
# Format:
#   'period_name': ['era1', 'era2', ...]
#
# These periods will be used to create era-combined datacards
# Note: Summary files will ONLY use 'eras_all' by default

ERAS_TO_COMBINE = {
    'eras_22': [
        '2022',
        '2022EE'
    ],
    
    'eras_23': [
        '2023',
        '2023BPix'
    ],
    
    'eras_all': [
        '2022',
        '2022EE',
        '2023',
        '2023BPix'
    ],
}


# ==============================================================================
# EXAMPLES OF OTHER CONFIGURATIONS
# ==============================================================================

# Example: Split by b-tag multiplicity
# SELECTIONS = {
#     'low_btag': ['SL_res_3j_1b', 'SL_res_4j_1b'],
#     'high_btag': ['SL_res_3j_2b', 'SL_res_4j_2b'],
# }

# Example: All resolved channels together
# SELECTIONS = {
#     'all_resolved': [
#         'SL_3j_resolved',
#         'SL_4j_resolved',
#         'SL_res_3j_1b',
#         'SL_res_3j_2b',
#         'SL_res_4j_1b',
#         'SL_res_4j_2b'
#     ],
# }

# Example: Separate Run 2 and Run 3 
# ERAS_TO_COMBINE = {
#     'run2': ['2016', '2017', '2018'],
#     'run3': ['2022', '2022EE', '2023', '2023BPix'],
#     'all_eras': ['2016', '2017', '2018', '2022', '2022EE', '2023', '2023BPix'],
# }