export const HERO_CONTENT = {
  greeting: "Hello, I'm",
  name: "Ajay Susanth",
  title: "Backend Engineer • AI Applications • Cloud • DevOps",
  introduction: "I design and build production-grade backend systems, intelligence-driven applications, and resilient cloud architectures. This portfolio is powered by an interactive hybrid RAG pipeline grounded in my engineering documents.",
  ctas: {
    chat: { label: "Ask the AI", href: "#chat" },
    resume: { label: "Resume", href: "/resume" },
    hire: { label: "Hire Me", href: "/hire" },
    github: { label: "GitHub", href: "https://github.com/AjaySusanth" }
  }
};

export const ROLE_BADGES = [
  "Backend Engineer",
  "AI Applications",
  "Cloud",
  "DevOps"
];

export const HIGHLIGHT_CARDS = [
  {
    id: "current-focus",
    icon: "🚀",
    title: "Current Focus",
    description: "Building production-grade RAG systems, vector database retrievers, and scalable backend services."
  },
  {
    id: "flagship-project",
    icon: "🧠",
    title: "Flagship Project",
    description: "RAG-Powered Developer Portfolio featuring hybrid search, pgvector indexing, and Redis caching.",
    badges: ["FastAPI", "Next.js", "Redis", "pgvector", "Docker"]
  },
  {
    id: "core-stack",
    icon: "⚙️",
    title: "Core Stack",
    description: "Primary engineering stack for development, data persistence, infrastructure, and deployment.",
    badges: ["Python", "FastAPI", "PostgreSQL", "Redis", "Azure", "Docker"]
  }
];

export const PROMPT_SUGGESTIONS = [
  { id: "about", text: "Tell me about yourself" },
  { id: "projects", text: "What projects have you built?" },
  { id: "rag", text: "Explain your RAG architecture" },
  { id: "tech", text: "What technologies do you use?" },
  { id: "availability", text: "Are you available for hiring?" }
];

export const EMPTY_CHAT_CONTENT = {
  welcomeTitle: "Ask the AI Portfolio Assistant",
  welcomeDescription: "Query my background, systems engineering projects, stack, or cloud experience using natural language. The response is generated dynamically and grounded strictly in verified portfolio documents.",
};
