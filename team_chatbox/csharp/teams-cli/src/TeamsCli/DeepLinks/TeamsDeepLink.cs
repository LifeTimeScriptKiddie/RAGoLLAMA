using System.Diagnostics;
using System.Web;

namespace TeamsCli.DeepLinks;

public static class TeamsDeepLink
{
    public static void OpenChat(string chatId, string? message = null)
    {
        var baseUrl = "msteams:/l/chat/0/0";
        var queryParams = new List<string> { $"users={chatId}" };
        
        if (!string.IsNullOrEmpty(message))
        {
            queryParams.Add($"message={HttpUtility.UrlEncode(message)}");
        }
        
        var deepLink = $"{baseUrl}?{string.Join("&", queryParams)}";
        
        try
        {
            var processStart = new ProcessStartInfo
            {
                FileName = deepLink,
                UseShellExecute = true
            };
            
            Process.Start(processStart);
            Console.WriteLine($"Opened Teams chat: {chatId}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to open Teams chat: {ex.Message}");
            Console.WriteLine($"Deep link: {deepLink}");
        }
    }
}