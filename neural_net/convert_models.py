from neural_net.nn_utils import convert_model_to_onnx
from pathlib import Path


dirs = [
    Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Final_Model/0807_JetTop/roster_3j4j/multi_HH_ttbar_tW_u360_4j/Pass0'),
    Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Final_Model/0807_JetTop/roster_3j4j/multi_HH_ttbar_tWandWJets_u360_4j/Pass4'),
    Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Final_Model/0807_JetTop/roster_3j4j/multi_HH_ttbar_WJets_u360_4j/Pass0')
]

for dir_path in dirs:
    best_ckpt = dir_path / "best_checkpoint"
    print(f'Converting model in: {str(best_ckpt)}')
    convert_model_to_onnx(best_ckpt, dir_path)