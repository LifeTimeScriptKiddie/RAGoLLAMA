using TeamsCli.Auth;

namespace TeamsCli.Commands;

public class LoginCommand
{
    private readonly AuthService _authService;

    public LoginCommand(AuthService authService)
    {
        _authService = authService;
    }

    public async Task<int> ExecuteAsync()
    {
        try
        {
            Console.WriteLine("Starting authentication...");
            var userPrincipalName = await _authService.LoginAsync();
            Console.WriteLine($"Successfully authenticated as: {userPrincipalName}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Authentication failed: {ex.Message}");
            return 1;
        }
    }
}