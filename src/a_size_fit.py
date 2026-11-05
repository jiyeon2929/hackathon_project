"""A. 사이즈/핏 예측 베이스라인 (Rent the Runway)
사용: python src/a_size_fit.py data/rtr/renttherunway_final_data.json.gz
"""
import gzip, json, re, sys
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

path = sys.argv[1]
with gzip.open(path, "rt", encoding="utf-8") as f:
    df = pd.DataFrame([json.loads(line) for line in f])
df.columns = [c.replace(" ", "_") for c in df.columns]
print("rows:", len(df))
print(df["fit"].value_counts(normalize=True).round(3).to_dict())


def height_in(s):
    m = re.match(r"(\d+)' ?(\d+)", str(s))
    return int(m.group(1)) * 12 + int(m.group(2)) if m else np.nan


def bust(s):
    m = re.match(r"(\d+)([a-z+/]+)", str(s))
    return (float(m.group(1)), m.group(2)) if m else (np.nan, None)


df["height"] = df["height"].map(height_in)
df["weight"] = pd.to_numeric(df["weight"].str.replace("lbs", ""), errors="coerce")
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df["size"] = pd.to_numeric(df["size"], errors="coerce")
b = df["bust_size"].map(bust)
df["band"] = b.map(lambda x: x[0])
df["cup"] = b.map(lambda x: x[1])
df["bmi"] = df["weight"] / (df["height"] ** 2) * 703

y_map = {"small": 0, "fit": 1, "large": 2}
df["y"] = df["fit"].map(y_map)

train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["y"])
train, test = train.copy(), test.copy()

# 학습 데이터에서만 계산한 통계 (테스트 정보 누출 방지)
# 상품: 이 상품은 보통 작게/크게 나오나?
g = train.groupby("item_id")
item = pd.DataFrame({
    "item_n": g.size(),
    "item_small": g["y"].apply(lambda s: (s == 0).mean()),
    "item_large": g["y"].apply(lambda s: (s == 2).mean()),
    "item_size_med": g["size"].median(),
})
# 사용자: 평소 입는 사이즈
user = train.groupby("user_id")["size"].median().rename("user_size_med")

for d in (train, test):
    d[item.columns] = d[["item_id"]].join(item, on="item_id")[item.columns].values
    d["user_size_med"] = d["user_id"].map(user)
    d["size_vs_user"] = d["size"] - d["user_size_med"]
    d["size_vs_item"] = d["size"] - d["item_size_med"]

cats = ["cup", "body_type", "category", "rented_for"]
for c in cats:
    train[c] = train[c].astype("category")
    test[c] = pd.Categorical(test[c], categories=train[c].cat.categories)

feats = ["size", "height", "weight", "age", "band", "bmi", "item_n", "item_small",
         "item_large", "item_size_med", "user_size_med", "size_vs_user", "size_vs_item"] + cats

model = lgb.LGBMClassifier(objective="multiclass", n_estimators=400, learning_rate=0.05,
                           num_leaves=63, class_weight="balanced", verbose=-1)
model.fit(train[feats], train["y"])
pred = model.predict(test[feats])

base = np.ones(len(test))  # 항상 "맞음"이라고 하는 기준선
print("\n== 결과 ==")
print(f"기준선(항상 '맞음') 정확도 {accuracy_score(test.y, base):.3f}  macro-F1 {f1_score(test.y, base, average='macro'):.3f}")
print(f"모델                정확도 {accuracy_score(test.y, pred):.3f}  macro-F1 {f1_score(test.y, pred, average='macro'):.3f}")
print(classification_report(test.y, pred, target_names=["small", "fit", "large"], digits=3))

imp = pd.Series(model.booster_.feature_importance("gain"), index=feats).sort_values(ascending=False)
print("중요 변수 TOP 8:", (imp / imp.sum()).head(8).round(3).to_dict())
