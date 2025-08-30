using System.Text.Json;
using System.Text.RegularExpressions;
using TeamsCli.Graph;

namespace TeamsCli.Commands;

public class ChatTailCommand
{
    private readonly GraphClient _graphClient;
    private readonly string _deltaDirectory;

    public ChatTailCommand(GraphClient graphClient)
    {
        _graphClient = graphClient;
        _deltaDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "teams-cli");
        Directory.CreateDirectory(_deltaDirectory);
    }

    public async Task<int> ExecuteAsync(string chatId, string? sinceFile = null, int timeoutSec = 0)
    {
        try
        {
            var deltaFile = Path.Combine(_deltaDirectory, $"delta-{chatId}.txt");
            string? deltaLink = null;

            if (!string.IsNullOrEmpty(sinceFile) && File.Exists(sinceFile))
            {
                deltaLink = await File.ReadAllTextAsync(sinceFile);
            }
            else if (File.Exists(deltaFile))
            {
                deltaLink = await File.ReadAllTextAsync(deltaFile);
            }

            Console.WriteLine($"Starting to tail chat {chatId}. Press Ctrl+C to stop.");

            var cts = new CancellationTokenSource();
            if (timeoutSec > 0)
            {
                cts.CancelAfter(TimeSpan.FromSeconds(timeoutSec));
            }

            Console.CancelKeyPress += (sender, e) =>
            {
                e.Cancel = true;
                cts.Cancel();
            };

            while (!cts.Token.IsCancellationRequested)
            {
                try
                {
                    var endpoint = string.IsNullOrEmpty(deltaLink) 
                        ? Endpoints.ChatMessagesDelta(chatId) 
                        : deltaLink;

                    var response = await _graphClient.GetAsync(endpoint);
                    var messageResponse = JsonSerializer.Deserialize<MessageListResponse>(response.RootElement.GetRawText());

                    if (messageResponse?.Value != null)
                    {
                        foreach (var message in messageResponse.Value.OrderBy(m => m.CreatedDateTime))
                        {
                            var timestamp = message.CreatedDateTime?.ToString("yyyy-MM-dd HH:mm:ss") ?? "Unknown";
                            var author = message.From?.User?.UserPrincipalName ?? "Unknown";
                            var content = ExtractTextFromHtml(message.Body?.Content ?? "");
                            
                            Console.WriteLine($"[{timestamp}Z] {author}: {content}");
                        }
                    }

                    if (!string.IsNullOrEmpty(messageResponse?.DeltaLink))
                    {
                        deltaLink = messageResponse.DeltaLink;
                        await File.WriteAllTextAsync(deltaFile, deltaLink);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error polling messages: {ex.Message}");
                }

                await Task.Delay(5000, cts.Token);
            }

            return 0;
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("\nStopped tailing chat.");
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to tail chat: {ex.Message}");
            return 1;
        }
    }

    private string ExtractTextFromHtml(string html)
    {
        if (string.IsNullOrEmpty(html))
            return "";

        var text = Regex.Replace(html, "<[^>]*>", "");
        text = System.Net.WebUtility.HtmlDecode(text);
        return text.Trim();
    }
}