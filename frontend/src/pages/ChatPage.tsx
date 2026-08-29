import { useParams } from "react-router-dom";
import { useEffect } from "react";
import ChatWindow from "@/components/ChatWindow";
import { useChat } from "@/hooks/useChat";

export default function ChatPage() {
  const { conversationId } = useParams();
  const { messages, sending, sendMessage, loadConversation } = useChat(conversationId);

  useEffect(() => {
    if (conversationId) loadConversation(conversationId);
  }, [conversationId, loadConversation]);

  return <ChatWindow messages={messages} sending={sending} onSend={sendMessage} />;
}