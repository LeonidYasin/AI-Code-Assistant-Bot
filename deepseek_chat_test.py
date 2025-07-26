import os
from huggingface_hub import InferenceClient
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

class DeepSeekChat:
    def __init__(self, model="deepseek-ai/DeepSeek-V3-0324"):
        self.client = InferenceClient()
        self.model = model
        self.console = Console()
        self.messages = []
        
    def print_welcome(self):
        self.console.print(Panel.fit(
            "🤖 [bold green]DeepSeek Chat Assistant[/]\n"
            "Type 'exit' to end the conversation",
            title="Welcome"
        ))
    
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
    
    def get_response(self):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=1024,
                temperature=0.7
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error: {str(e)}"
    
    def display_message(self, role, content):
        if role == "user":
            self.console.print(Panel.fit(
                content,
                title="You",
                border_style="blue",
                style="white"
            ))
        else:
            md = Markdown(content)
            self.console.print(Panel.fit(
                md,
                title="Assistant",
                border_style="green",
                style="white"
            ))
    
    def run(self):
        self.print_welcome()
        
        while True:
            user_input = self.console.input("[bold blue]You: [/]")
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                self.console.print("👋 Goodbye!")
                break
                
            self.add_message("user", user_input)
            
            with self.console.status("[bold green]Thinking...[/]"):
                response = self.get_response()
                self.add_message("assistant", response)
            
            self.display_message("assistant", response)

if __name__ == "__main__":
    chat = DeepSeekChat()
    chat.run()