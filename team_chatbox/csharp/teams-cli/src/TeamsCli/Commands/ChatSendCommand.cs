using System.Text.Json;
using TeamsCli.Graph;

namespace TeamsCli.Commands;

public class ChatSendCommand
{
    private readonly GraphClient _graphClient;

    public ChatSendCommand(GraphClient graphClient)
    {
        _graphClient = graphClient;
    }

    public async Task<int> ExecuteAsync(string chatId, string text, bool html = false)
    {
        try
        {
            var contentType = html ? "html" : "text";
            
            var message = new SendMessageRequest
            {
                Body = new MessageBody
                {
                    ContentType = contentType,
                    Content = text
                }
            };

            var response = await _graphClient.PostJsonAsync(Endpoints.PostChatMessage(chatId), message);
            var responseContent = await response.Content.ReadAsStringAsync();
            
            var messageResponse = JsonSerializer.Deserialize<Message>(responseContent);
            Console.WriteLine($"Message sent successfully. ID: {messageResponse?.Id}");
            
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to send message: {ex.Message}");
            return 1;
        }
    }
}