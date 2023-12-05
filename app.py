import boto3
import re
import random
from flask import Flask, jsonify, render_template
# DynamoDB クライアントを作成
dynamodb = boto3.client('dynamodb')

# DynamoDB リソースを作成
dynamodb_resource = boto3.resource("dynamodb")

# NG リストのテーブル名を指定
ng_list_table_name = "NG_list"

# word_list テーブル名を指定
word_list_table_name = "word_list"

# NG リストを取得する関数
def get_ng_list_from_dynamodb():
    ng_list_table = dynamodb_resource.Table(ng_list_table_name)
    response = ng_list_table.scan()
    ng_list = [item["Read"] for item in response["Items"]]
    return ng_list

# word_list を取得する関数
def get_word_list_from_dynamodb():
    word_list_table = dynamodb_resource.Table(word_list_table_name)
    response = word_list_table.scan()
    word_list = [item["Read"] for item in response["Items"]]
    return word_list

# 使用済み単語のリスト（最初は空）
use_list = []

# NG リストと word_list を取得
ng_list = get_ng_list_from_dynamodb()
word_list = get_word_list_from_dynamodb()
# NG リストを取得
ng_list = get_ng_list_from_dynamodb()

# 使用済み単語リストに単語を追加する関数
def add_word_to_use_list(word):
    """
    使用した単語をDynamoDBに追加する関数
    :param word: 使用する単語
    """
    use_list.append(word)  # ローカルリストに単語を追加

def add_request_to_add_word(request_word):
    """
    単語をDynamoDBから追加するためのリクエストを作成し、追加する関数
    :param request_word: 削除する単語
    """
    request_word_table = dynamodb_resource.Table("request_word")

    # 既存のリクエストを確認
    existing_item = request_word_table.get_item(Key={'Read': request_word}).get('Item')
    
    if existing_item:
        # 既存のリクエストがある場合、カウントを増やす
        existing_request_count = existing_item.get('request_count', 0)
        request_count = existing_request_count + 1
    else:
        # リクエストが存在しない場合、カウントを1で初期化
        request_count = 1

    # 新しいリクエストまたは更新リクエストを作成
    request = {
        "Read": request_word,
        "request_type": "add",
        "request_count": request_count
    }

    try:
        # DynamoDB にリクエストを追加または更新
        request_word_table.put_item(Item=request)
        print(f"追加リクエストを送信しました: {request_word}")
    except Exception as e:
        print(f"リクエスト送信に失敗しました: {str(e)}")

    return

def remove_request_to_add_word(request_word):
    """
    単語をDynamoDBから削除するためのリクエストを作成し、追加する関数
    :param request_word: 削除する単語
    """
    request_word_table = dynamodb_resource.Table("request_word")

    # 既存のリクエストを確認
    existing_item = request_word_table.get_item(Key={'Read': request_word}).get('Item')
    
    if existing_item:
        # 既存のリクエストがある場合、カウントを増やす
        existing_request_count = existing_item.get('request_count', 0)
        request_count = existing_request_count + 1
    else:
        # リクエストが存在しない場合、カウントを1で初期化
        request_count = 1

    # 新しいリクエストまたは更新リクエストを作成
    request = {
        "Read": request_word,
        "request_type": "remove",
        "request_count": request_count
    }

    try:
        # DynamoDB にリクエストを追加または更新
        request_word_table.put_item(Item=request)
        print(f"削除リクエストを送信しました: {request_word}")
    except Exception as e:
        print(f"リクエスト送信に失敗しました: {str(e)}")

    return

# ひらがなで構成され、2文字以上であり、最後に「ん」が含まれないかをチェックする関数
def check_string(input_str, ng_list):
    hiragana_pattern = r'^[\u3040-\u309Fー]+$' 
    
    if (re.match(hiragana_pattern, input_str) is not None) and (len(input_str) >= 2) and (not input_str.endswith("ん")):
        return True
    else:
        return False

# 初期頭文字（キーワード）を設定
while True:
    current_head_character = input("初手の頭文字（ひらがなのみ、'ん'を含まない）を入力してください: ")
    if re.match(r'^[\u3041-\u3093]+$', current_head_character):  # ひらがなの範囲を指定
        break
    else:
        print("無効な入力です。ひらがなのみで、'ん'を含まない頭文字を入力してください。")

def generate_cpu_word(current_head_character, used_words, ng_list, word_list):
    global last_cpu_word  # グローバル変数として last_cpu_word を宣言

    # 使用可能な単語の候補を探す
    candidates = [word for word in word_list if word.startswith(ending_character) and word not in used_words and word not in ng_list]

    if candidates:
        # 候補がある場合はランダムに1つ選択
        cpu_word = random.choice(candidates)
        last_cpu_word = cpu_word  # CPUが生成した単語を記録
        return cpu_word
    else:
        # 使用可能な単語がない場合はNoneを返す
        return None
    
def generate_cpu_word1(current_head_character, ending_character, used_words, ng_list, word_list):
    # 使用可能な単語の候補を探す
    candidates = [word for word in word_list if word.startswith(current_head_character) and word.endswith(ending_character) and word not in used_words and word not in ng_list]

    if candidates:
        # 候補がある場合はランダムに1つ選択
        cpu_word = random.choice(candidates)
        last_cpu_word = cpu_word  # CPUが生成した単語を記録
        return cpu_word
    else:
        # 使用可能な単語がない場合はNoneを返す
        return None
    
# 小さいひらがなを大きいひらがなに変換するためのマッピング
small_to_large_hiragana = {
    "ぁ": "あ", "ぃ": "い", "ぅ": "う", "ぇ": "え", "ぉ": "お",
    "っ": "つ", "ゃ": "や", "ゅ": "ゆ", "ょ": "よ", "ゎ": "わ"
}

# 頭文字を設定する関数
def set_head_character(word):
    last_char = word[-1]  # 最後の文字

    # "ー" で終わる単語の場合、1つ前のひらがなに変換
    if last_char == "ー" and len(word) >= 2:
        previous_char = word[-2]
        
        # 1つ前の文字もひらがなであれば変換
        if previous_char in small_to_large_hiragana:
            last_char = small_to_large_hiragana[previous_char]

    # 小さいひらがながあれば、対応する大きいひらがなに変換
    last_char = small_to_large_hiragana.get(last_char, last_char)
    
    return last_char

# ユーザーによる単語入力を受け付ける関数
auto_count = 0
def validate_word(word, current_head_character, ending_character, used_words, ng_list):
    # 単語の条件チェック
    if word in used_words or word in ng_list:
        return False, "既に使用された単語です。"
    if not check_string(word, ng_list):  # ここで ng_list を渡す
        return False, "無効な単語形式です。"
    if word[0] != current_head_character or not word.endswith(ending_character):
        return False, "頭文字または末尾の文字が一致しません。"
    return True, ""


last_cpu_word = ""
def user_input_word(current_head_character, ending_character, ng_list, word_list):
    global auto_count
    global last_cpu_word

    while True:
        input_word = input(f"{current_head_character} から始まり、{ending_character}で終わる単語を入力してください: ")

        if input_word.lower() in ["q", "ｑ"]:
            print("ゲームを終了します")
            if auto_count > 0:
                print(f"オート機能は {auto_count} 回使用されました。")
            return None  # ここで関数から抜け出す
        
        if input_word.lower() in ["m", "ｍ"]:
            if last_cpu_word:
                print(f"CPUの単語「{last_cpu_word}」をキャンセルします。")
                remove_request_to_add_word(last_cpu_word)

                # CPUに新しい単語を生成させる
                cpu_word = generate_cpu_word(current_head_character, use_list, ng_list, get_word_list_from_dynamodb())
                if cpu_word:
                    print(f"CPUの新しい単語: {cpu_word}")
                    last_cpu_word = cpu_word  # CPUの最新の単語を更新
                    add_word_to_use_list(cpu_word)  # 使用済みリストに追加
                    current_head_character = cpu_word[-1]
                else:
                    print("CPUが新しい単語を生成できませんでした。")
            else:
                print("前回のCPUの単語が存在しません。")
            continue
        
        if input_word in ["auto", "ａｕｔｏ"]:
            if mode_choice == "1":
                auto_count += 1
                auto_word = generate_cpu_word1(current_head_character, ending_character, use_list, ng_list, word_list)
                
                if auto_word:
                    print(f"自動生成された単語: {auto_word}")
                    return auto_word
                else:
                    print("自動生成に失敗しました。ゲームを終了します。")
                    break
            
        if input_word not in ["auto", "ａｕｔｏ", "q", "ｑ", "m", "ｍ"]:
            ending_character = set_head_character(input_word)
                
        valid, message = validate_word(input_word, current_head_character, ending_character, use_list, ng_list)
        if not valid:
            print(message)
            continue

        # 未登録単語のハンドリング
        if input_word not in word_list:
            user_decision = input(f"「{input_word}」は登録されていない単語です。リクエストして使用しますか？ (y/n): ")
            if user_decision.lower() in ["y", "ｙ"]:
                add_request_to_add_word(input_word)
                return input_word  # 単語を使用リストに追加して続行
            elif user_decision.lower() in ["n", "ｎ"]:
                continue
            else:
                print("無効な入力です。")
                continue

        return input_word
    
def user_input_word2(current_head_character, ending_character, ng_list, word_list):
    global auto_count
    global last_cpu_word

    while True:
        input_word = input(f"{current_head_character} から始まる単語を入力してください: ")

        if input_word.lower() in ["q", "ｑ"]:
            print("ゲームを終了します")
            if auto_count > 0:
                print(f"オート機能は {auto_count} 回使用されました。")
            return None  # ここで関数から抜け出す
        
        if input_word.lower() in ["m", "ｍ"]:
            if last_cpu_word:
                print(f"CPUの単語「{last_cpu_word}」をキャンセルします。")
                remove_request_to_add_word(last_cpu_word)

                # モード2では、CPUは指定された末尾文字で終わる単語を生成する
                cpu_word = generate_cpu_word1(current_head_character, ending_character, use_list, ng_list, get_word_list_from_dynamodb())
                if cpu_word:
                    print(f"CPUの新しい単語: {cpu_word}")
                    last_cpu_word = cpu_word  # CPUの最新の単語を更新
                    add_word_to_use_list(cpu_word)  # 使用済みリストに追加
                    current_head_character = set_head_character(cpu_word)
                else:
                    print("CPUが新しい単語を生成できませんでした。")
            else:
                print("前回のCPUの単語が存在しません。")
            continue
        
        if input_word in ["auto", "ａｕｔｏ"]:
                auto_count += 1
                auto_word = generate_cpu_word1(current_head_character, ending_character, use_list, ng_list, word_list)
                
                if auto_word:
                    print(f"自動生成された単語: {auto_word}")
                    return auto_word
                else:
                    print("自動生成に失敗しました。ゲームを終了します。")
                    break
            
        if input_word not in ["auto", "ａｕｔｏ", "q", "ｑ", "m", "ｍ"]:
            ending_character = set_head_character(input_word)
                
        valid, message = validate_word(input_word, current_head_character, ending_character, use_list, ng_list)
        if not valid:
            print(message)
            continue

        # 未登録単語のハンドリング
        if input_word not in word_list:
            user_decision = input(f"「{input_word}」は登録されていない単語です。リクエストして使用しますか？ (y/n): ")
            if user_decision.lower() in ["y", "ｙ"]:
                add_request_to_add_word(input_word)
                return input_word  # 単語を使用リストに追加して続行
            elif user_decision.lower() in ["n", "ｎ"]:
                continue
            else:
                print("無効な入力です。")
                continue

        return input_word

# ゲームモード選択
print("ゲームモードを選択してください:")
print("1. CPUに「〇」攻めをするモード")
print("2. CPUから「〇」攻めを受けるモード")
mode_choice = input("モードを選んでください (1または2): ")

if mode_choice == "1":
    while True:
        ending_character = input("末尾の文字として使用するひらがな1文字を入力してください: ")
        if re.match(r'^[\u3040-\u309F]$', ending_character):  # 1文字のひらがなをチェック
            break
        else:
            print("無効な入力です。ひらがな1文字を入力してください。")
    while True:
        # プレイヤーの単語入力
        input_word = user_input_word(current_head_character, ending_character, ng_list, word_list)  # CPUにもう一回単語を出す
        add_word_to_use_list(input_word)  # ローカルリストへの追加
        
        if input_word is None:  # None をチェック
            break  # ループを終了

        # CPUの単語を生成する

        cpu_word = generate_cpu_word(current_head_character, use_list, ng_list, word_list)
        
        if cpu_word:
            print(f"CPUの単語: {cpu_word}")
            add_word_to_use_list(cpu_word)  # ローカルリストへの追加

            # 次の頭文字を更新
            current_head_character = set_head_character(cpu_word)
        else:
            print("CPUが単語を生成できませんでした。ゲーム終了。")
            if auto_count > 0:
                print(f"オート機能は {auto_count} 回使用されました。")
            break
elif mode_choice == "2":
    while True:
        ending_character = input("CPUが使用する末尾のひらがな1文字を入力してください: ")
        if re.match(r'^[\u3040-\u309F]$', ending_character):
            break
        else:
            print("無効な入力です。ひらがな1文字を入力してください。")

    # CPUの初回単語を生成
    cpu_word = generate_cpu_word1(current_head_character, ending_character, use_list, ng_list, word_list)
    last_cpu_word = cpu_word
    if cpu_word:
        print(f"CPUの単語: {cpu_word}")
        add_word_to_use_list(cpu_word)
        current_head_character = set_head_character(cpu_word)  # 次の頭文字を設定
    else:
        print("CPUが単語を生成できませんでした。ゲーム終了。")

    while True:
        # プレイヤーのターン
        input_word = user_input_word2(current_head_character, ending_character, ng_list, word_list)
        if input_word is None:
            break
        add_word_to_use_list(input_word)
        current_head_character = set_head_character(input_word)

        # CPUのターン
        cpu_word = generate_cpu_word1(current_head_character, ending_character, use_list, ng_list, word_list)
        if cpu_word:
            print(f"CPUの単語: {cpu_word}")
            last_cpu_word = cpu_word
            add_word_to_use_list(cpu_word)
            current_head_character = set_head_character(cpu_word)
        else:
            print("CPUが単語を生成できませんでした。ゲーム終了。")
            break
else:
    print("無効なモードが選択されました。1または2を入力してください。")
