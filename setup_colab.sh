#!/bin/bash
# =============================================================
#  setup_colab.sh
#  在 Google Colab 執行此腳本以還原本機開發環境
#  包含：基礎 DL、NLP/BERTopic、多模態圖文對齊（CLIP 系列）
#
#  使用方式（Colab cell 內執行）：
#    !bash setup_colab.sh
# =============================================================

set -e   # 任何步驟失敗即中止

echo "======================================"
echo " 🚀 開始安裝 Colab 環境套件..."
echo "======================================"

# ----------------------------------------------------------
# 1. 核心深度學習框架
# ----------------------------------------------------------
echo ""
echo "📦 [1/8] 安裝 PyTorch 生態系 ..."
pip install torch torchvision torchaudio \
    pytorch-lightning \
    torchmetrics \
    timm

# ----------------------------------------------------------
# 2. 資料科學基礎套件
# ----------------------------------------------------------
echo ""
echo "📦 [2/8] 安裝資料科學基礎套件 ..."
pip install numpy scipy pandas matplotlib seaborn xgboost

# ----------------------------------------------------------
# 3. NLP / BERTopic 相關
# ----------------------------------------------------------
echo ""
echo "📦 [3/8] 安裝 NLP 套件 ..."
pip install bertopic jieba nltk scikit-learn

# ----------------------------------------------------------
# 4. 下載 NLTK 停用詞資料
# ----------------------------------------------------------
echo ""
echo "📦 [4/8] 下載 NLTK stopwords ..."
python3 -c "import nltk; nltk.download('stopwords', quiet=True)"

# ----------------------------------------------------------
# 5. 其他工具套件
# ----------------------------------------------------------
echo ""
echo "📦 [5/8] 安裝其他工具 ..."
pip install pypdf tqdm pyyaml

# ----------------------------------------------------------
# 6. 多模態核心：圖文對齊 / 檢索（CLIP 系列）
#    - transformers : 載入 CLIP、ALIGN、SigLIP、BLIP 等
#    - accelerate   : 多 GPU / 混合精度訓練支援
#    - datasets     : HuggingFace 圖文資料集
#    - peft         : LoRA fine-tune，Colab 可跑大模型
#    - bitsandbytes : 4-bit/8-bit 量化，節省 VRAM
#    - open-clip-torch : OpenCLIP，CLIP 開源強化版
#    - sentence-transformers : 文字 embedding 對齊
# ----------------------------------------------------------
echo ""
echo " [6/8] 安裝多模態框架（CLIP / 圖文對齊）..."
pip install transformers accelerate datasets \
    peft \
    bitsandbytes \
    open-clip-torch \
    sentence-transformers

# ----------------------------------------------------------
# 7. 圖像處理強化
#    - Pillow        : 基礎圖像讀寫（transformers 相依）
#    - albumentations: 進階圖像資料增強
#    - einops        : Tensor reshape，ViT/Attention 常用
# ----------------------------------------------------------
echo ""
echo "📦 [7/8] 安裝圖像處理套件 ..."
pip install Pillow albumentations einops

# ----------------------------------------------------------
# 8. 驗證關鍵套件是否正常載入
# ----------------------------------------------------------
echo ""
echo "🔍 [8/8] 驗證安裝結果 ..."
python3 - <<'EOF'
packages = {
    # 基礎 DL
    "torch":                "PyTorch",
    "pytorch_lightning":    "PyTorch Lightning",
    "timm":                 "timm",
    # 資料科學
    "numpy":                "NumPy",
    "pandas":               "pandas",
    "matplotlib":           "Matplotlib",
    "seaborn":              "Seaborn",
    "sklearn":              "scikit-learn",
    "scipy":                "SciPy",
    "xgboost":              "XGBoost",
    # NLP / BERTopic
    "bertopic":             "BERTopic",
    "jieba":                "jieba",
    "nltk":                 "NLTK",
    # 多模態核心
    "transformers":         "Transformers (HuggingFace)",
    "accelerate":           "Accelerate",
    "datasets":             "Datasets (HuggingFace)",
    "peft":                 "PEFT (LoRA)",
    "open_clip":            "OpenCLIP",
    "sentence_transformers":"Sentence-Transformers",
    # 圖像工具
    "PIL":                  "Pillow",
    "albumentations":       "Albumentations",
    "einops":               "einops",
}

ok, fail = [], []
for mod, name in packages.items():
    try:
        __import__(mod)
        ok.append(name)
    except ImportError:
        fail.append(name)

print(f"\n✅ 成功 ({len(ok)}): {', '.join(ok)}")
if fail:
    print(f"❌ 失敗 ({len(fail)}): {', '.join(fail)}")
else:
    print("🎉 所有套件安裝成功！")
EOF

echo ""
echo "======================================"
echo " ✅ 環境安裝完成！"
echo ""
echo " 💡 多模態快速起手範例："
echo "    from transformers import CLIPModel, CLIPProcessor"
echo "    import open_clip"
echo "======================================"
