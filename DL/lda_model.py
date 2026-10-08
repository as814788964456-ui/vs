import pandas as pd
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import ssl

# 略過 Mac 環境下的 SSL 憑證驗證，以便順利下載外部資料
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def load_data():
    """
    載入外部開源數據集 (以 20 Newsgroups 為例)
    """
    print("正在載入 20 newsgroups 數據集...")
    # 為了示範速度，我們只選取 4 個類別的數據
    categories = ['alt.atheism', 'talk.religion.misc', 'comp.graphics', 'sci.space']
    dataset = fetch_20newsgroups(subset='train', categories=categories, shuffle=True, random_state=42)
    print(f"成功載入 {len(dataset.data)} 篇文檔。\n")
    return dataset.data

def preprocess_data(data):
    """
    文本預處理：將文本轉換為詞頻矩陣 (Document-Term Matrix)
    """
    print("進行文本預處理與向量化...")
    # 使用 CountVectorizer，自動去除英文停用詞，
    # 忽略出現頻率高於 95% 或低於 2 篇文檔的詞。
    vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
    doc_term_matrix = vectorizer.fit_transform(data)
    print(f"詞頻矩陣建立完成，形狀 (文檔數, 詞彙數): {doc_term_matrix.shape}\n")
    return doc_term_matrix, vectorizer

def train_lda_model(doc_term_matrix, n_components=4, alpha=None, beta=None):
    """
    訓練 LDA 模型，支援自訂 Alpha 與 Beta 超參數。
    在 sklearn 中，Alpha 對應 doc_topic_prior，Beta 對應 topic_word_prior。
    若設定為 None，sklearn 預設會使用 1 / n_components。
    """
    print(f"開始訓練 LDA 模型 (主題數={n_components}, Alpha={alpha}, Beta={beta})...")
    lda_model = LatentDirichletAllocation(
        n_components=n_components, 
        doc_topic_prior=alpha,
        topic_word_prior=beta,
        max_iter=10, 
        learning_method='online', 
        random_state=42,
        n_jobs=-1
    )
    lda_model.fit(doc_term_matrix)
    print("模型訓練完成。\n")
    return lda_model

def display_topics(model, vectorizer, top_n_words=10):
    """
    印出每個主題中最具代表性的前 N 個單詞
    """
    print(f"展示各主題的前 {top_n_words} 個代表詞彙:")
    feature_names = vectorizer.get_feature_names_out()
    
    for topic_idx, topic in enumerate(model.components_):
        print(f"Topic #{topic_idx}:")
        # 依據權重由大到小排序，取得前 N 個單詞的索引
        top_features_ind = topic.argsort()[:-(top_n_words + 1):-1]
        top_features = [feature_names[i] for i in top_features_ind]
        print(" | ".join(top_features))

def calculate_coherence_score(model, vectorizer, data, top_n_words=10):
    """
    計算各主題的 Coherence Score (c_v)
    我們使用 sklearn 訓練的模型，並透過 gensim 輔助計算 coherence
    """
    try:
        from gensim.corpora import Dictionary
        from gensim.models.coherencemodel import CoherenceModel
    except ImportError:
        print("\n[提示] 計算 Coherence Score 需要安裝 gensim 模組。")
        print("請在終端機輸入 'pip install gensim' 來安裝。")
        return None

    print("\n正在計算 Coherence Score (這可能需要一點時間)...")
    
    # 1. 取得文本的斷詞結果 (Tokenized texts)
    # 利用原來的 CountVectorizer 的 analyzer 將文本斷詞
    analyzer = vectorizer.build_analyzer()
    texts = [analyzer(doc) for doc in data]
    
    # 2. 建立 Gensim 所需的 Dictionary
    dictionary = Dictionary(texts)
    
    # 3. 從 sklearn 模型中擷取每個主題的前 N 個詞彙
    feature_names = vectorizer.get_feature_names_out()
    topics = []
    for topic_weights in model.components_:
        top_feature_ind = topic_weights.argsort()[:-(top_n_words + 1):-1]
        topic_words = [feature_names[i] for i in top_feature_ind]
        topics.append(topic_words)
        
    # 4. 呼叫 Gensim CoherenceModel 計算 c_v 分數
    cm = CoherenceModel(topics=topics, texts=texts, dictionary=dictionary, coherence='c_v')
    
    # 整體平均 Coherence Score
    coherence_avg = cm.get_coherence()
    print(f"整體模型的 Coherence Score (c_v): {coherence_avg:.4f}")
    
    # 每個主題的 Coherence Score
    coherence_per_topic = cm.get_coherence_per_topic()
    for idx, score in enumerate(coherence_per_topic):
        print(f"  ► Topic #{idx} Coherence Score: {score:.4f}")
        
    return coherence_avg, coherence_per_topic

def main():
    # 1. 資料導入 (Data Import)
    data = load_data()
    
    # 2. 文本預處理 (Text Preprocessing)
    doc_term_matrix, vectorizer = preprocess_data(data)
    
    # 3. 建立並訓練模型 (Model Training)
    # 這裡因為我們載入了 4 個分類的文章，所以我們設定 n_components=4
    lda_model = train_lda_model(doc_term_matrix, n_components=4)
    
    # 4. 輸出主題結果 (Display Results)
    display_topics(lda_model, vectorizer, top_n_words=15)
    
    # 5. 計算並輸出 Coherence Score
    calculate_coherence_score(lda_model, vectorizer, data, top_n_words=15)

if __name__ == "__main__":
    main()
