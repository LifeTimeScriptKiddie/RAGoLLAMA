using System.Text.Json;
using TeamsCli.Graph;
using TeamsCli.Util;

namespace TeamsCli.Commands;

public class ChatsListCommand
{
    private readonly GraphClient _graphClient;

    public ChatsListCommand(GraphClient graphClient)
    {
        _graphClient = graphClient;
    }

    public async Task<int> ExecuteAsync(int? top = null, bool json = false)
    {
        try
        {
            var response = await _graphClient.GetAsync(Endpoints.MeChats(top));
            
            if (json)
            {
                Console.WriteLine(response.RootElement.GetRawText());
                return 0;
            }

            var chatListResponse = JsonSerializer.Deserialize<ChatListResponse>(response.RootElement.GetRawText());
            
            if (chatListResponse?.Value == null || !chatListResponse.Value.Any())
            {
                Console.WriteLine("No chats found.");
                return 0;
            }

            var table = new ConsoleTable("Chat ID", "Topic/Name", "Type", "Last Updated");

            foreach (var chat in chatListResponse.Value)
            {
                var topic = string.IsNullOrEmpty(chat.Topic) ? "(no topic)" : chat.Topic;
                var lastUpdated = chat.LastUpdatedDateTime?.ToString("yyyy-MM-dd HH:mm:ss") ?? "Unknown";
                
                table.AddRow(
                    chat.Id ?? "", 
                    topic, 
                    chat.ChatType ?? "", 
                    lastUpdated
                );
            }

            table.Print();
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to get chats: {ex.Message}");
            return 1;
        }
    }
}