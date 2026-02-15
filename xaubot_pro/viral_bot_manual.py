#!/usr/bin/env python3
"""
Viral TikTok Bot - Manual URL Version
Simplified for manual URL input workflow
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json
import os
import time
from datetime import datetime
import threading

# Import from original
from viral_bot import VideoProcessor, TikTokUploader, ConfigManager, DOWNLOADS_DIR, PROCESSED_DIR, LOGS_DIR

class ManualViralBotGUI:
    """Simplified GUI for manual URL input"""

    def __init__(self, root):
        self.root = root
        self.root.title("Viral TikTok Bot - Manual URL Mode")
        self.root.geometry("800x700")

        # Load config
        self.config = ConfigManager.load_config()
        self.accounts = ConfigManager.load_accounts()

        # Create directories
        for d in [DOWNLOADS_DIR, PROCESSED_DIR, LOGS_DIR]:
            os.makedirs(d, exist_ok=True)

        # Create UI
        self.create_ui()

        # Queue for videos
        self.video_queue = []
        self.processing = False

    def create_ui(self):
        """Build the simplified GUI"""

        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Manual URLs
        urls_tab = ttk.Frame(notebook)
        notebook.add(urls_tab, text='📥 Add URLs')
        self.create_urls_tab(urls_tab)

        # Tab 2: Queue & Processing
        queue_tab = ttk.Frame(notebook)
        notebook.add(queue_tab, text='📤 Process & Upload')
        self.create_queue_tab(queue_tab)

        # Tab 3: Accounts
        accounts_tab = ttk.Frame(notebook)
        notebook.add(accounts_tab, text='🔐 TikTok Accounts')
        self.create_accounts_tab(accounts_tab)

        # Tab 4: Settings
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text='⚙️ Settings')
        self.create_settings_tab(settings_tab)

    def create_urls_tab(self, parent):
        """Manual URL input tab"""

        # Instructions
        inst_frame = ttk.LabelFrame(parent, text="📋 Instructions")
        inst_frame.pack(fill='x', padx=10, pady=10)

        instructions = """
1. Paste video URLs below (YouTube, TikTok, Instagram, etc.)
2. One URL per line
3. Click "Add to Queue"
4. Videos will be downloaded, transformed, and uploaded automatically!
        """
        ttk.Label(inst_frame, text=instructions, justify='left').pack(padx=10, pady=10)

        # URL input
        url_frame = ttk.LabelFrame(parent, text="🎬 Paste URLs Here")
        url_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.urls_text = scrolledtext.ScrolledText(url_frame, height=15, width=70, font=('Consolas', 10))
        self.urls_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.urls_text.insert('1.0', '# Paste URLs here (one per line)\n# Example:\n# https://www.youtube.com/watch?v=dQw4w9WgXcQ\n# https://youtube.com/shorts/xxxxx\n# https://www.tiktok.com/@user/video/xxxxx\n\n')

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="✅ Add to Queue", command=self.add_urls_to_queue, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear", command=lambda: self.urls_text.delete('1.0', tk.END)).pack(side='left', padx=5)

        # Status
        self.url_status = ttk.Label(parent, text="Ready to add URLs", foreground="green")
        self.url_status.pack(pady=5)

    def create_queue_tab(self, parent):
        """Processing and upload queue"""

        # Queue list
        queue_frame = ttk.LabelFrame(parent, text="📋 Video Queue")
        queue_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('Title', 'Account', 'Status')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.queue_tree.heading(col, text=col)

        self.queue_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', padx=10, pady=10)

        self.process_btn = ttk.Button(btn_frame, text="▶️ Start Processing", command=self.start_processing)
        self.process_btn.pack(side='left', padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_processing, state='disabled')
        self.stop_btn.pack(side='left', padx=5)

        ttk.Button(btn_frame, text="🗑️ Clear Queue", command=self.clear_queue).pack(side='left', padx=5)

        # Progress
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=5)

        # Log
        log_frame = ttk.LabelFrame(parent, text="📝 Processing Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state='disabled', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

    def create_accounts_tab(self, parent):
        """Account management"""

        from viral_bot import ViralBotGUI
        temp_gui = ViralBotGUI(tk.Tk())
        temp_gui.root.withdraw()
        temp_gui.create_accounts_tab(parent)
        self.accounts_listbox = temp_gui.accounts_listbox
        self.refresh_accounts_list = temp_gui.refresh_accounts_list
        self.add_account = temp_gui.add_account
        self.remove_account = temp_gui.remove_account
        self.test_login = temp_gui.test_login
        temp_gui.root.destroy()

    def create_settings_tab(self, parent):
        """Settings"""

        transform_frame = ttk.LabelFrame(parent, text="Video Transformation")
        transform_frame.pack(fill='x', padx=10, pady=10)

        self.resize_var = tk.BooleanVar(value=self.config.get('video_transformation', {}).get('resize', True))
        ttk.Checkbutton(transform_frame, text="✅ Resize to TikTok format (9:16)", variable=self.resize_var).pack(anchor='w', padx=5, pady=2)

        speed_frame = ttk.Frame(transform_frame)
        speed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(speed_frame, text="Speed multiplier:").pack(side='left')
        self.speed_var = ttk.Spinbox(speed_frame, from_=0.8, to=1.3, increment=0.05, width=10)
        self.speed_var.set(self.config.get('video_transformation', {}).get('speed_change', 1.05))
        self.speed_var.pack(side='left', padx=5)

        ttk.Button(parent, text="💾 Save Settings", command=self.save_settings).pack(pady=20)

    def add_urls_to_queue(self):
        """Add URLs from text box to queue"""

        urls_text = self.urls_text.get('1.0', tk.END)
        urls = [line.strip() for line in urls_text.split('\n') if line.strip() and not line.strip().startswith('#')]

        if not urls:
            messagebox.showwarning("No URLs", "Please paste some URLs first!")
            return

        if not self.accounts:
            messagebox.showwarning("No Accounts", "Please add TikTok accounts first!")
            return

        import random
        added = 0

        for url in urls:
            # Simple URL validation
            if not url.startswith('http'):
                continue

            # Random account
            account = random.choice(self.accounts)

            self.video_queue.append({
                'video': {
                    'title': f"Video from {url[:50]}...",
                    'url': url,
                    'upvotes': 0,
                    'subreddit': 'manual',
                    'permalink': url
                },
                'account': account['name'],
                'status': 'Pending'
            })
            added += 1

        self.refresh_queue()
        self.url_status.config(text=f"✅ Added {added} URLs to queue!", foreground="green")
        messagebox.showinfo("Success", f"Added {added} videos to queue!\n\nGo to 'Process & Upload' tab to start.")

    def refresh_queue(self):
        """Refresh queue display"""
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)

        for item in self.video_queue:
            self.queue_tree.insert('', 'end', values=(
                item['video']['title'][:50],
                item['account'],
                item['status']
            ))

    def start_processing(self):
        """Start processing queue - same as original"""
        if not self.video_queue:
            messagebox.showwarning("Empty Queue", "No videos in queue")
            return

        self.processing = True
        self.process_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.start()

        threading.Thread(target=self.process_queue, daemon=True).start()

    def stop_processing(self):
        """Stop processing"""
        self.processing = False
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.log("⏹️ Processing stopped by user")

    def process_queue(self):
        """Process all videos - download, transform, upload"""

        for i, item in enumerate(self.video_queue):
            if not self.processing:
                break

            self.log(f"\n[{i+1}/{len(self.video_queue)}] Processing: {item['video']['title']}")

            # Update status
            item['status'] = 'Downloading'
            self.refresh_queue()

            # Download
            self.log("📥 Downloading video...")
            video_path = VideoProcessor.download_video(item['video']['url'])

            if not video_path:
                self.log("❌ Download failed")
                item['status'] = 'Failed - Download'
                self.refresh_queue()
                continue

            self.log(f"✅ Downloaded: {video_path}")

            # Transform
            item['status'] = 'Transforming'
            self.refresh_queue()

            self.log("🎬 Transforming for TikTok...")
            output_path = os.path.join(PROCESSED_DIR, f"tiktok_{int(time.time())}.mp4")

            transform_config = {
                'resize': self.resize_var.get(),
                'speed_change': float(self.speed_var.get())
            }

            success = VideoProcessor.transform_for_tiktok(video_path, output_path, transform_config)

            if not success:
                self.log("❌ Transform failed")
                item['status'] = 'Failed - Transform'
                self.refresh_queue()
                continue

            self.log(f"✅ Transformed: {output_path}")

            # Upload
            item['status'] = 'Uploading'
            self.refresh_queue()

            self.log(f"📤 Uploading to: {item['account']}")
            caption = f"{item['video']['title'][:100]} 🔥 #viral #fyp"

            upload_success = TikTokUploader.upload_video(output_path, caption, item['account'])

            if upload_success:
                self.log("✅ Upload successful!")
                item['status'] = 'Completed'

                # Update account stats
                for acc in self.accounts:
                    if acc['name'] == item['account']:
                        acc['videos_posted'] += 1
                ConfigManager.save_accounts(self.accounts)
            else:
                self.log("❌ Upload failed")
                item['status'] = 'Failed - Upload'

            self.refresh_queue()

            # Cleanup
            try:
                os.remove(video_path)
            except:
                pass

        self.progress.stop()
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log("\n✅ Queue processing complete!")

    def clear_queue(self):
        """Clear queue"""
        if messagebox.askyesno("Confirm", "Clear entire queue?"):
            self.video_queue.clear()
            self.refresh_queue()

    def save_settings(self):
        """Save settings"""
        self.config['video_transformation'] = {
            'resize': self.resize_var.get(),
            'speed_change': float(self.speed_var.get())
        }

        ConfigManager.save_config(self.config)
        messagebox.showinfo("Success", "Settings saved!")

    def log(self, message):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')


def main():
    """Launch manual URL version"""
    root = tk.Tk()
    app = ManualViralBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
