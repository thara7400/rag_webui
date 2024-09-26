from abc import ABC, abstractmethod
import json
import openai

# データをベクトル化するモジュールのインターフェース
class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def save(self, texts: list[str], filename: str) -> bool:
        raise NotImplementedError

# Embedderインターフェースの実装
class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def embed(self, texts: list[str]) -> list[list[float]]:
        # openai 1.10.0 で動作確認
        # "'$.input' is invalid.": https://github.com/chroma-core/chroma/issues/709
        response = openai.embeddings.create(input=texts, model="text-embedding-3-small")
        # レスポンスからベクトルを抽出
        return [data.embedding for data in response.data]

    def save(self, texts: list[str], filename: str) -> bool:
        vectors = self.embed(texts)
        data_to_save = [
            {"id": idx, "text": text, "vector": vector}
            for idx, (text, vector) in enumerate(zip(texts, vectors))
        ]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"{filename} に保存されました。")
        return True

# 関数として定義
def get_embedding(text: str, api_key: str) -> list[float]:
    embedder = OpenAIEmbedder(api_key)
    embedded_vector = embedder.embed([text])[0]
    return embedded_vector
def save_embeddings(texts: list[str], filename: str, api_key: str) -> bool:
    embedder = OpenAIEmbedder(api_key)
    return embedder.save(texts, filename)
