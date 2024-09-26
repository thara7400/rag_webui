document.addEventListener("DOMContentLoaded", function() {
    // 埋め込みファイルリストを動的に取得してチェックボックスを生成
    fetch("/embedding_files/")
        .then(response => response.json())
        .then(data => {
            const container = document.querySelector(".checkbox-container");
            data.files.forEach(file => {
                const label = document.createElement("label");
                label.innerHTML = `<input type="checkbox" name="embedding_files" value="${file}"> ${file}<br>`;
                container.appendChild(label);
            });
        })
        .catch(error => console.error("参照情報の取得中にエラーが発生しました:", error));

    // ファイルアップロードボタンのクリックイベント処理
    const uploadButton = document.getElementById("upload-button");
    uploadButton.addEventListener("click", function() {
        const uploadForm = document.getElementById("upload-form");

        // ファイルが選択されているかを確認
        const fileInput = uploadForm.querySelector("input[type='file']");
        if (!fileInput.files.length) {
            alert("ファイルを選択してください。");
            return;
        }

        const formData = new FormData(uploadForm);
        fetch(uploadForm.getAttribute("action"), {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                alert(`ファイルが正常にアップロードされました。\n${data.embedding_filename}`);
                location.reload();
            } else {
                alert("ファイルのアップロードに失敗しました。再試行してください。");
            }
        })
        .catch(error => console.error("ファイルアップロード中にエラーが発生しました:", error));
    });

    // チャットボタンのクリックイベント処理
    const chatButton = document.getElementById("chat-button");
    chatButton.addEventListener("click", function() {
        const chatForm = document.getElementById("chat-form");

        // テキストが入力されているかを確認
        const text = chatForm.querySelector("[name='user_query']");
        if (!text.value.trim()) {
            alert("質問を入力してください。");
            return;
        }

        const formData = new FormData(chatForm);
        const responseBox = document.querySelector(".response-box");
        // 「問い合わせ中」のメッセージを表示
        responseBox.innerHTML = "<p>問い合わせ中...</p>";
        // タイムアウト処理の設定（10秒）
        const fetchWithTimeout = (url, options, timeout = 10000) => {
            return new Promise((resolve, reject) => {
                const timer = setTimeout(() => {
                    reject(new Error("問い合わせがタイムアウトしました。"));
                }, timeout);
                fetch(url, options)
                    .then(response => {
                        clearTimeout(timer);
                        resolve(response);
                    })
                    .catch(err => {
                        clearTimeout(timer);
                        reject(err);
                    });
            });
        };
        fetchWithTimeout(chatForm.getAttribute("action"), {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const userQuery = formData.get("user_query");
            responseBox.innerHTML = `
                <h3>あなたの質問:</h3>
                <p>${userQuery}</p>
                <h3>RAG Botの応答:</h3>
                <p>${data.response}</p>
                <h3>参照した情報:</h3>
                <p>${data.combined_texts}</p>
            `;
            // 質問ボックスの中身を空にする
            chatForm.querySelector("[name='user_query']").value = "";
        })
        .catch(error => {
            responseBox.innerHTML = `<p style="color: red;">${error.message}</p>`;
            console.error("問い合わせ中にエラーが発生しました:", error);
        });
    });
});
