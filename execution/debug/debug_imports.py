import sys

with open("debug_output.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    
    print(f"Sys Path: {sys.path}")
    try:
        import langchain
        print(f"LangChain file: {langchain.__file__}")
        print(f"LangChain version: {langchain.__version__}")
    except Exception as e:
        print(f"LangChain import failed: {e}")

    try:
        from langchain.agents import AgentExecutor
        print("✅ AgentExecutor found")
    except ImportError as e:
        print(f"❌ AgentExecutor failed: {e}")

    try:
        from langchain.agents import create_tool_calling_agent
        print("✅ create_tool_calling_agent found")
    except ImportError as e:
        print(f"❌ create_tool_calling_agent failed: {e}")

