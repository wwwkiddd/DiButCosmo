document.getElementById("bot-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const botToken = document.getElementById("bot_token").value;
    const adminId = document.getElementById("admin_id").value;

    try {
        const response = await fetch("https://dibutcosmo.ru/create_bot/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ bot_token: botToken, admin_id: adminId })
        });

        const result = await response.json();
        if (result.status === "ok") {
            const username = result.username || "your_bot";
            document.getElementById("result").innerHTML = `✅ Бот создан! Вот ссылка: <a href="https://t.me/${username}" target="_blank">https://t.me/${username}</a>`;
        } else {
            document.getElementById("result").innerText = "❌ Ошибка создания бота.";
        }
    } catch (error) {
        document.getElementById("result").innerText = "❌ Ошибка подключения к серверу.";
        console.error(error);
    }
});
