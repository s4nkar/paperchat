import type { ChatMessage } from "../types";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  return <div>{message.content}</div>;
}
