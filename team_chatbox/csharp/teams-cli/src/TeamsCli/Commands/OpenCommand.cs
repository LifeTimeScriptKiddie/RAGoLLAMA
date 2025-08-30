using TeamsCli.DeepLinks;

namespace TeamsCli.Commands;

public class OpenCommand
{
    public async Task<int> ExecuteAsync(string chatId, string? message = null)
    {
        try
        {
            TeamsDeepLink.OpenChat(chatId, message);
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to open Teams chat: {ex.Message}");
            return 1;
        }
    }
}