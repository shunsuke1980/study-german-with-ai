#!/usr/bin/env python3
"""
File watcher for German vocabulary word files
Monitors data/words/ directory and automatically generates content when new files are added
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WordFileHandler(FileSystemEventHandler):
    """Handler for word file changes"""
    
    def __init__(self):
        self.processed_files = set()
        self.last_processed = {}
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        self.process_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        # Avoid processing the same file too frequently
        current_time = time.time()
        if event.src_path in self.last_processed:
            if current_time - self.last_processed[event.src_path] < 5:  # 5 second cooldown
                return
        
        self.last_processed[event.src_path] = current_time
        self.process_file_event(event.src_path, "modified")
    
    def process_file_event(self, file_path, event_type):
        """Process a word file event"""
        file_path = Path(file_path)
        
        # Only process .txt files
        if file_path.suffix.lower() != '.txt':
            return
        
        # Check if file exists and is readable
        if not file_path.exists() or not file_path.is_file():
            return
        
        print(f"\n🔔 Word file {event_type}: {file_path.name}")
        
        # Wait a moment for file to be fully written
        time.sleep(2)
        
        # Check if file has content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                print(f"⚠️  File {file_path.name} is empty, skipping")
                return
            
            words = [line.strip() for line in content.split('\n') if line.strip()]
            if len(words) < 3:
                print(f"⚠️  File {file_path.name} has too few words ({len(words)}), skipping")
                return
            
            print(f"📝 Found {len(words)} words in {file_path.name}")
            
        except Exception as e:
            print(f"❌ Error reading file {file_path.name}: {e}")
            return
        
        # Avoid processing the same file multiple times
        file_key = f"{file_path.name}-{file_path.stat().st_mtime}"
        if file_key in self.processed_files:
            print(f"⏭️  File {file_path.name} already processed, skipping")
            return
        
        self.processed_files.add(file_key)
        
        # Run the vocabulary content generator
        self.run_content_generator()
    
    def run_content_generator(self):
        """Run the vocabulary content generator script"""
        print("🚀 Running vocabulary content generator...")
        
        script_path = Path("generate_vocab_content.py")
        if not script_path.exists():
            print("❌ generate_vocab_content.py not found")
            return
        
        try:
            # Run the content generator
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Content generation completed successfully")
                print("📄 Output:")
                print(result.stdout)
                
                # If running in git repository, auto-commit
                if self.is_git_repo():
                    self.auto_commit()
            else:
                print("❌ Content generation failed")
                print("Error output:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏱️  Content generation timed out")
        except Exception as e:
            print(f"❌ Error running content generator: {e}")
    
    def is_git_repo(self):
        """Check if current directory is a git repository"""
        return Path(".git").exists()
    
    def auto_commit(self):
        """Auto-commit generated content to git"""
        print("🔄 Auto-committing generated content...")
        
        try:
            # Add generated files
            subprocess.run(["git", "add", "_posts/", "assets/audio/", "data/ssml/"], 
                         capture_output=True, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "diff", "--staged", "--quiet"], 
                                  capture_output=True)
            
            if result.returncode != 0:  # There are staged changes
                # Commit with timestamp
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Auto-generated vocabulary content ({timestamp})"
                
                subprocess.run(["git", "commit", "-m", commit_msg], 
                             capture_output=True, check=True)
                
                print("✅ Changes committed to git")
            else:
                print("ℹ️  No changes to commit")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Git commit failed: {e}")

def setup_environment():
    """Check and setup the environment"""
    print("🔧 Setting up environment...")
    
    # Check required directories
    required_dirs = ["data/words", "_posts", "assets/audio", "data/ssml"]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ensured: {dir_path}")
    
    # Check for required scripts
    required_files = ["generate_vocab_content.py"]
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file missing: {file_path}")
            return False
    
    # Check environment variables
    required_env = ["ANTHROPIC_API_KEY"]
    optional_env = ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    for env_var in required_env:
        if env_var not in os.environ:
            print(f"❌ Required environment variable missing: {env_var}")
            return False
        print(f"✅ Environment variable found: {env_var}")
    
    for env_var in optional_env:
        if env_var in os.environ:
            print(f"✅ Optional environment variable found: {env_var}")
        else:
            print(f"ℹ️  Optional environment variable not set: {env_var} (audio generation will be skipped)")
    
    return True

def scan_existing_files(handler):
    """Scan for existing word files that haven't been processed"""
    words_dir = Path("data/words")
    if not words_dir.exists():
        return
    
    print("🔍 Scanning for existing word files...")
    
    # Find all .txt files
    txt_files = list(words_dir.glob("*.txt"))
    if not txt_files:
        print("ℹ️  No existing word files found")
        return
    
    print(f"📄 Found {len(txt_files)} word files")
    
    # Check which files have corresponding blog posts
    posts_dir = Path("_posts")
    if posts_dir.exists():
        existing_episodes = list(posts_dir.glob("*-german-vocab-episode-*.md"))
        episode_count = len(existing_episodes)
        print(f"📚 Found {episode_count} existing vocabulary episodes")
    else:
        episode_count = 0
    
    # If there are more word files than episodes, process the latest one
    if len(txt_files) > episode_count:
        latest_file = max(txt_files, key=lambda f: f.stat().st_mtime)
        print(f"🔄 Processing latest unprocessed word file: {latest_file.name}")
        handler.process_file_event(str(latest_file), "existing")

def main():
    """Main function to start the file watcher"""
    print("👁️  German Vocabulary File Watcher Started")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Initialize handler
    event_handler = WordFileHandler()
    
    # Scan for existing files
    scan_existing_files(event_handler)
    
    # Setup file watcher
    observer = Observer()
    watch_dir = "data/words"
    
    if not Path(watch_dir).exists():
        print(f"❌ Watch directory does not exist: {watch_dir}")
        sys.exit(1)
    
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    
    print(f"👀 Watching directory: {Path(watch_dir).absolute()}")
    print("📝 Monitoring for .txt word files...")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("✅ File watcher stopped")

if __name__ == "__main__":
    main()