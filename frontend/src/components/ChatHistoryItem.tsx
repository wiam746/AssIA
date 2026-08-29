import { Link } from "react-router-dom";
import type { Conversation } from "@/types";

interface ChatHistoryItemProps {
  conversation: Conversation;
  active?: boolean;
}

export default function ChatHistoryItem({ conversation, active }: ChatHistoryItemProps) {
  return (
    <Link
      to={`/chat/${conversation.id}`}
      className={`block truncate rounded px-2 py-2 text-sm transition ${
        active ? "bg-accent/20 text-accent" : "text-white/70 hover:bg-white/5"
      }`}
    >
      {conversation.title}
    </Link>
  );
}