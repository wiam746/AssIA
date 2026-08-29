import { useState, useCallback } from "react";
import api from "@/hooks/useApi";
import type { ChatResponse, Conversation, Message } from "@/types";

export function useChat(initialConversationId?: string) {
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);

  const loadConversation = useCallback(async (id: string) => {
    const res = await api.get<Conversation>(`/chat/conversations/${id}`);
    setConversationId(res.data.id);
    setMessages(res.data.messages);
  }, []);

  const sendMessage = useCallback(
    async (text: string, documentIds?: string[]) => {
      setSending(true);
      const optimisticMessage: Message = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticMessage]);

      try {
        const res = await api.post<ChatResponse>("/chat/messages", {
          conversation_id: conversationId,
          message: text,
          document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
        });
        setConversationId(res.data.conversation_id);
        setMessages((prev) => [...prev, res.data.message]);
      } finally {
        setSending(false);
      }
    },
    [conversationId]
  );

  return { conversationId, messages, sending, sendMessage, loadConversation };
}