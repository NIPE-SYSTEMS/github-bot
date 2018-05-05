import aiohttp.web
import aiotg
import asyncio
import os
import sys
import yaml
import uuid as uuidlib

class Config:
	def __init__(self):
		with open(sys.argv[1]) as f:
			self.yaml = yaml.load(f)["github-bot"]
	
	def save(self):
		with open(sys.argv[1], "w") as f:
			yaml.dump({
				"github-bot": self.yaml
			}, f, default_flow_style=False)
	
	def get_chat_by_uuid(self, uuid):
		for chat_uuid, chat_id in self.yaml["chats"].items():
			if chat_uuid == uuid:
				return { "uuid": chat_uuid, "id": chat_id }
	
	def get_chat_by_id(self, id):
		for chat_uuid, chat_id in self.yaml["chats"].items():
			if chat_id == id:
				return { "uuid": chat_uuid, "id": chat_id }
	
	def register_chat(self, id):
		print("Register", id, "...")
		if str(id) not in self.yaml["chats"].values():
			self.yaml["chats"][str(uuidlib.uuid4())] = id
		self.save()
	
	def unregister_chat(self, id):
		print("Unregister", id, "...")
		self.yaml["chats"] = { chat_uuid: chat_id for chat_uuid, chat_id in self.yaml["chats"].items() if chat_id != id }
		self.save()
	
	@property
	def baseurl(self): return self.yaml["baseurl"]
	@property
	def token(self): return self.yaml["token"]
	@property
	def uuids(self): return self.yaml["uuids"]

class Repository:
	def __init__(self, json):
		self.name = json.get("repository", {}).get("full_name", "<Unknown>").replace("[", "(").replace("]", ")")
		self.url = json.get("repository", {}).get("html_url", "https://github.com/404").replace("(", "%28").replace(")", "%29")

class Branch:
	def __init__(self, json):
		self.branch = json.get("ref", "<Unknown>").replace("refs/heads/", "")

class Commit:
	def __init__(self, json_subset):
		self.description = json_subset.get("message", "<Unknown>")
		self.url = json_subset.get("url", "https://github.com/404")
		self.committer = json_subset.get("committer", {}).get("name", "<Unknown>")

class Commits:
	def __init__(self, json):
		self.commits = []
		for commit in json.get("commits", []):
			self.commits.append(Commit(commit))

class Zen:
	def __init__(self, json):
		self.zen = json.get("zen", "<Unknown>")

class PushEvent:
	def __init__(self, json):
		self.repository = Repository(json)
		self.branch = Branch(json)
		self.commits = Commits(json)
	
	@property
	def message(self):
		repository = "*Repository:* [{}]({})".format(self.repository.name.replace("*", ""), self.repository.url.replace("*", ""))
		branch = "*Branch:* {}".format(self.branch.branch.replace("*", ""))
		commits = "\n".join([ "- [{}]({}) (by {})".format(commit.description, commit.url, commit.committer) for commit in self.commits.commits ])
		return "{}\n{}\n\n{}".format(repository, branch, commits)

class PingEvent:
	def __init__(self, json):
		self.repository = Repository(json)
		self.zen = Zen(json)
	
	@property
	def message(self):
		repository = "[{}]({})".format(self.repository.name.replace("*", ""), self.repository.url.replace("*", ""))
		return "GitHub just sent me a *ping event* to notice you that your webhook at {} has been created! 💪\nThey also told me: {} 😉".format(repository, self.zen.zen)

class GithubBot:
	def __init__(self):
		self.config = Config()
		self.bot = aiotg.Bot(api_token=self.config.token)
		self.bot.add_command(r"^/start", self.handle_start)
		self.bot.add_command(r"^/status", self.handle_status)
		self.bot.add_command(r"^/guide", self.handle_guide)
		self.bot.add_command(r"^/register", self.handle_register)
		self.bot.add_command(r"^/unregister", self.handle_unregister)
		self.app = aiohttp.web.Application()
		self.app.router.add_post("/{uuid}", self.handle_webhook)
	
	def run(self):
		loop = asyncio.get_event_loop()
		loop.run_until_complete(self.run_app())
	
	async def run_app(self):
		runner = aiohttp.web.AppRunner(self.app)
		await runner.setup()
		site = aiohttp.web.TCPSite(runner)
		await site.start()
		await self.bot.loop()
		await runner.cleanup()
	
	async def handle_start(self, chat, match):
		await chat.send_text("You want push notifications of your GitHub repositories posted in this chat?\n\nI can help you with that by providing you with an URL for GitHub webhooks.")
		await self.handle_status(chat, match)
	
	async def handle_guide(self, chat, match):
		saved_chat = self.config.get_chat_by_id(chat.id)
		if saved_chat == None:
			await chat.send_text("*Guide:*\n\n*First you need to* /register *this chat to follow the* /guide.", parse_mode="Markdown")
		else:
			await chat.send_text("*Guide:*\n\nThe URL for this chat is:\n`{}`\n\nYou can use this URL for different repositories. If you're using it all push notifications will be posted here. Feel free to repeat the steps below for multiple repositories in order to receive notifications from them.".format(self.config.baseurl.format(uuid=saved_chat["uuid"])), parse_mode="Markdown")
			await chat.send_photo(photo="https://nipe-systems.de/github-bot/screenshot_1-3.png", caption="1. Go into your repository settings.\n2. Click on \"Webhooks\"\n3. Select \"Add webhook\"")
			await chat.send_photo(photo="https://nipe-systems.de/github-bot/screenshot_4-7.png", caption="4. Enter the URL\n5. Select \"application/json\"\n6. Enable \"Just the push event\"\n7. Click \"Add webhook\"")
	
	async def handle_status(self, chat, match):
		saved_chat = self.config.get_chat_by_id(chat.id)
		if saved_chat == None:
			await chat.send_text("*Status:*\n\n❌ Who are you? Don't have any ID of you. 😥\n\nGo ahead and /register this chat so that I can send GitHub notifications in here! 😃", parse_mode="Markdown")
		else:
			await chat.send_text("*Status:*\n\n✔ This chat is registered. 😃\n\nThe following URL can be used for GitHub webhooks:\n`{}`\nSee the /guide on how to do that.\n\nYou can also /unregister this chat if you want. 😉".format(self.config.baseurl.format(uuid=saved_chat["uuid"])), parse_mode="Markdown")
	
	async def handle_register(self, chat, match):
		self.config.register_chat(chat.id)
		await self.handle_status(chat, match)
	
	async def handle_unregister(self, chat, match):
		self.config.unregister_chat(chat.id)
		await self.handle_status(chat, match)
	
	async def handle_webhook(self, request):
		uuid = request.match_info["uuid"]
		try:
			json = await request.json()
		except:
			return aiohttp.web.Response(status=400)
		if request.headers["X-GitHub-Event"] == "push":
			push_event = PushEvent(json)
			try:
				chat = aiotg.Chat(bot=self.bot, chat_id=int(self.config.get_chat_by_uuid(uuid)["id"]))
			except AttributeError:
				return aiohttp.web.Response(status=404)
			await chat.send_text(push_event.message, parse_mode="Markdown")
			return aiohttp.web.json_response({ "ok": True })
		elif request.headers["X-GitHub-Event"] == "ping":
			ping_event = PingEvent(json)
			try:
				chat = aiotg.Chat(bot=self.bot, chat_id=int(self.config.get_chat_by_uuid(uuid)["id"]))
			except AttributeError:
				return aiohttp.web.Response(status=404)
			await chat.send_text(ping_event.message, parse_mode="Markdown")
			return aiohttp.web.json_response({ "ok": True })
		return aiohttp.web.Response(status=404)

GithubBot().run()
