
class TokenTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenTracker, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance
    
    def reset(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.calls = 0
        
    def track(self, usage: object):
        """
        Updates counts from a Groq/OpenAI usage object.
        Expected attributes: prompt_tokens, completion_tokens, total_tokens
        """
        if not usage:
            return
            
        p = getattr(usage, "prompt_tokens", 0)
        c = getattr(usage, "completion_tokens", 0)
        t = getattr(usage, "total_tokens", 0)
        
        self.prompt_tokens += p
        self.completion_tokens += c
        self.total_tokens += t
        self.calls += 1
        
    def get_summary(self):
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

    def print_summary(self):
        print("\n[TOKEN USAGE SUMMARY]")
        print(f"  LLM Calls:         {self.calls}")
        print(f"  Prompt Tokens:     {self.prompt_tokens}")
        print(f"  Completion Tokens: {self.completion_tokens}")
        print(f"  Total Tokens:      {self.total_tokens}")
        print("---------------------\n")

# Global instance accessor
tracker = TokenTracker()
