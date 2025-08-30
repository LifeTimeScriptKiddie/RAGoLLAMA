using Microsoft.Extensions.Configuration;
using System.CommandLine;
using TeamsCli.Auth;
using TeamsCli.Commands;
using TeamsCli.Graph;

namespace TeamsCli;

class Program
{
    static async Task<int> Main(string[] args)
    {
        var configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .Build();

        var authService = new AuthService(configuration);
        var graphBaseUrl = configuration["graphBaseUrl"] ?? "https://graph.microsoft.com/v1.0";
        var graphClient = new GraphClient(authService, graphBaseUrl);

        var rootCommand = new RootCommand("teams-cli - Microsoft Teams CLI tool");

        var loginCommand = new Command("login", "Authenticate with Microsoft Teams");
        loginCommand.SetHandler(async () =>
        {
            var cmd = new LoginCommand(authService);
            return await cmd.ExecuteAsync();
        });

        var meCommand = new Command("me", "Show current user information");
        meCommand.SetHandler(async () =>
        {
            var cmd = new MeCommand(graphClient);
            return await cmd.ExecuteAsync();
        });

        var chatsCommand = new Command("chats", "Chat-related commands");
        
        var chatsListCommand = new Command("ls", "List chats");
        var topOption = new Option<int?>("--top", "Number of chats to retrieve");
        var jsonOption = new Option<bool>("--json", "Output raw JSON");
        chatsListCommand.AddOption(topOption);
        chatsListCommand.AddOption(jsonOption);
        chatsListCommand.SetHandler(async (int? top, bool json) =>
        {
            var cmd = new ChatsListCommand(graphClient);
            return await cmd.ExecuteAsync(top, json);
        }, topOption, jsonOption);

        chatsCommand.AddCommand(chatsListCommand);

        var chatCommand = new Command("chat", "Individual chat commands");
        
        var chatSendCommand = new Command("send", "Send a message to a chat");
        var chatIdOption = new Option<string>("--chat", "Chat ID") { IsRequired = true };
        var textOption = new Option<string>("--text", "Message text") { IsRequired = true };
        var htmlOption = new Option<bool>("--html", "Send as HTML content");
        chatSendCommand.AddOption(chatIdOption);
        chatSendCommand.AddOption(textOption);
        chatSendCommand.AddOption(htmlOption);
        chatSendCommand.SetHandler(async (string chatId, string text, bool html) =>
        {
            var cmd = new ChatSendCommand(graphClient);
            return await cmd.ExecuteAsync(chatId, text, html);
        }, chatIdOption, textOption, htmlOption);

        var chatTailCommand = new Command("tail", "Tail messages from a chat");
        var tailChatIdOption = new Option<string>("--chat", "Chat ID") { IsRequired = true };
        var sinceOption = new Option<string?>("--since", "Delta URL file");
        var timeoutOption = new Option<int>("--timeout-sec", () => 0, "Timeout in seconds (0 = infinite)");
        chatTailCommand.AddOption(tailChatIdOption);
        chatTailCommand.AddOption(sinceOption);
        chatTailCommand.AddOption(timeoutOption);
        chatTailCommand.SetHandler(async (string chatId, string? since, int timeout) =>
        {
            var cmd = new ChatTailCommand(graphClient);
            return await cmd.ExecuteAsync(chatId, since, timeout);
        }, tailChatIdOption, sinceOption, timeoutOption);

        chatCommand.AddCommand(chatSendCommand);
        chatCommand.AddCommand(chatTailCommand);

        var openCommand = new Command("open", "Open a Teams chat");
        var openChatIdOption = new Option<string>("--chat", "Chat ID") { IsRequired = true };
        var messageOption = new Option<string?>("--message", "Pre-filled message");
        openCommand.AddOption(openChatIdOption);
        openCommand.AddOption(messageOption);
        openCommand.SetHandler(async (string chatId, string? message) =>
        {
            var cmd = new OpenCommand();
            return await cmd.ExecuteAsync(chatId, message);
        }, openChatIdOption, messageOption);

        rootCommand.AddCommand(loginCommand);
        rootCommand.AddCommand(meCommand);
        rootCommand.AddCommand(chatsCommand);
        rootCommand.AddCommand(chatCommand);
        rootCommand.AddCommand(openCommand);

        try
        {
            return await rootCommand.InvokeAsync(args);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return 1;
        }
        finally
        {
            graphClient.Dispose();
        }
    }
}