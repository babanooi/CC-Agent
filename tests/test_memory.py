"""测试记忆模块"""
import json
import os
import tempfile


class TestConversationMemory:
    def test_add_message(self):
        from memory.conversation import ConversationMemory
        mem = ConversationMemory(window_size=5)
        mem.add_message("user", "你好")
        mem.add_message("assistant", "你好！有什么可以帮助你的？")
        assert mem.turn_count == 1
        assert not mem.is_empty

    def test_context_string(self):
        from memory.conversation import ConversationMemory
        mem = ConversationMemory(window_size=5)
        mem.add_message("user", "测试问题")
        ctx = mem.get_context_string()
        assert "用户: 测试问题" in ctx or "测试问题" in ctx

    def test_chat_history_format(self):
        from memory.conversation import ConversationMemory
        mem = ConversationMemory()
        mem.add_message("user", "Q")
        history = mem.get_chat_history()
        assert history == [{"role": "user", "content": "Q"}]

    def test_clear(self):
        from memory.conversation import ConversationMemory
        mem = ConversationMemory()
        mem.add_message("user", "测试")
        mem.clear()
        assert mem.is_empty
        assert mem.turn_count == 0

    def test_window_overflow_triggers_compress(self):
        from memory.conversation import ConversationMemory
        mem = ConversationMemory(window_size=2)
        for i in range(6):
            mem.add_message("user", f"问题{i}")
            mem.add_message("assistant", f"回答{i}")
        assert len(mem.messages) <= mem.window_size * 2


class TestLongTermMemory:
    def test_create_and_persist(self):
        from memory.long_term import LongTermMemory
        ltm = LongTermMemory("pytest_user")
        ltm.update_profile({"budget": "5000"})
        ltm.add_preference("拍照")
        assert ltm.data["profile"]["budget"] == "5000"
        assert "拍照" in ltm.data["preferences"]
        # cleanup
        os.remove(ltm.file_path)

    def test_context_string(self):
        from memory.long_term import LongTermMemory
        ltm = LongTermMemory("pytest_user_2")
        ltm.update_profile({"usage": "游戏"})
        ctx = ltm.get_context_string()
        assert "游戏" in ctx
        os.remove(ltm.file_path)
