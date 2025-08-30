using System.Text.Json;
using TeamsCli.Graph;

namespace TeamsCli.Commands;

public class MeCommand
{
    private readonly GraphClient _graphClient;

    public MeCommand(GraphClient graphClient)
    {
        _graphClient = graphClient;
    }

    public async Task<int> ExecuteAsync()
    {
        try
        {
            var response = await _graphClient.GetAsync(Endpoints.Me());
            var user = JsonSerializer.Deserialize<User>(response.RootElement.GetRawText());

            Console.WriteLine($"Display Name: {user?.DisplayName}");
            Console.WriteLine($"User Principal Name: {user?.UserPrincipalName}");
            Console.WriteLine($"ID: {user?.Id}");

            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to get user information: {ex.Message}");
            return 1;
        }
    }
}