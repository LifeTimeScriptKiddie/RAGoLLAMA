using Microsoft.Identity.Client;
using Microsoft.Extensions.Configuration;
using System.Text.Json;

namespace TeamsCli.Auth;

public class AuthService
{
    private readonly IPublicClientApplication _app;
    private readonly string[] _scopes;
    private AuthenticationResult? _lastResult;

    public AuthService(IConfiguration configuration)
    {
        var tenantId = Environment.GetEnvironmentVariable("TENANT_ID") ?? configuration["tenantId"];
        var clientId = Environment.GetEnvironmentVariable("CLIENT_ID") ?? configuration["clientId"];
        
        var scopesConfig = Environment.GetEnvironmentVariable("SCOPES");
        _scopes = !string.IsNullOrEmpty(scopesConfig) 
            ? scopesConfig.Split(',', StringSplitOptions.RemoveEmptyEntries)
            : configuration.GetSection("scopes").Get<string[]>() ?? Array.Empty<string>();

        if (string.IsNullOrEmpty(tenantId) || string.IsNullOrEmpty(clientId))
            throw new InvalidOperationException("TenantId and ClientId must be configured");

        _app = PublicClientApplicationBuilder.Create(clientId)
            .WithAuthority($"https://login.microsoftonline.com/{tenantId}")
            .Build();

        InitializeCacheAsync().Wait();
    }

    private async Task InitializeCacheAsync()
    {
        var cacheHelper = await TokenCache.CreateAsync();
        cacheHelper.RegisterCache(_app.UserTokenCache);
    }

    public async Task<string> LoginAsync()
    {
        try
        {
            var accounts = await _app.GetAccountsAsync();
            AuthenticationResult? result = null;

            if (accounts.Any())
            {
                try
                {
                    result = await _app.AcquireTokenSilent(_scopes, accounts.FirstOrDefault()).ExecuteAsync();
                }
                catch (MsalUiRequiredException)
                {
                }
            }

            if (result == null)
            {
                result = await _app.AcquireTokenWithDeviceCode(_scopes, deviceCodeCallback =>
                {
                    Console.WriteLine(deviceCodeCallback.Message);
                    return Task.CompletedTask;
                }).ExecuteAsync();
            }

            _lastResult = result;
            return result.Account.Username;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Authentication failed: {ex.Message}", ex);
        }
    }

    public async Task<string> GetAccessTokenAsync()
    {
        try
        {
            var accounts = await _app.GetAccountsAsync();
            if (!accounts.Any())
                throw new InvalidOperationException("No authenticated account found. Please run 'login' command first.");

            var result = await _app.AcquireTokenSilent(_scopes, accounts.FirstOrDefault()).ExecuteAsync();
            _lastResult = result;
            return result.AccessToken;
        }
        catch (MsalUiRequiredException)
        {
            throw new InvalidOperationException("Interactive authentication required. Please run 'login' command.");
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Token acquisition failed: {ex.Message}", ex);
        }
    }

    public async Task<bool> IsAuthenticatedAsync()
    {
        try
        {
            var accounts = await _app.GetAccountsAsync();
            if (!accounts.Any()) return false;

            var result = await _app.AcquireTokenSilent(_scopes, accounts.FirstOrDefault()).ExecuteAsync();
            return result != null;
        }
        catch
        {
            return false;
        }
    }
}