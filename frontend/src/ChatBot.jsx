// frontend/src/ChatBot.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);

  // カテゴリ一覧をバックエンドから取得
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await axios.get("https://faq-chatbot-backend-gdfo.onrender.com/categories");

        setCategories(res.data.categories || []);
        //デフォルト未選択にするためコメントアウト
        //if (res.data.categories.length > 0) {
        //  setCategory(res.data.categories[0]);  // 初期選択
        //}
      } catch (err) {
        console.error("カテゴリの取得に失敗しました", err);
      }
    };
    fetchCategories();
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { type: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    try {
      const res = await axios.post("https://faq-chatbot-backend-gdfo.onrender.com/ask", {
        message: input,
        category: category
      });
      setMessages([...newMessages, { type: "bot", text: res.data.answer }]);
    } catch (error) {
      setMessages([...newMessages, { type: "bot", text: "エラーが発生しました。" }]);
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <div className="mb-2">
        <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリを選択:</label>
        <select
          className="border rounded w-full p-2 mb-2"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">-- カテゴリを選択（未選択＝全件） --</option>
          {categories.map((cat, idx) => (
            <option key={idx} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div className="border rounded p-2 h-96 overflow-y-scroll mb-2 bg-white">
        {messages.map((msg, idx) => (
          <div key={idx} className={`text-${msg.type === "user" ? "right" : "left"} my-1`}>
            <span className={`inline-block px-2 py-1 rounded ${msg.type === "user" ? "bg-blue-100" : "bg-gray-200"}`}>
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <div className="flex">
        <input
          className="border rounded w-full p-2 mr-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="質問を入力してください"
        />
        <button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={sendMessage}>送信</button>
      </div>
    </div>
  );
};

export default ChatBot;
