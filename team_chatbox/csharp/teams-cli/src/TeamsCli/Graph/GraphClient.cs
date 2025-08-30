using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using TeamsCli.Auth;
using TeamsCli.Util;

namespace TeamsCli.Graph;

public class GraphClient
{
    private readonly HttpClient _httpClient;
    private readonly AuthService _authService;
    private readonly string _baseUrl;

    public GraphClient(AuthService authService, string baseUrl)
    {
        _authService = authService;
        _baseUrl = baseUrl.TrimEnd('/');
        _httpClient = new HttpClient();
        _httpClient.DefaultRequestHeaders.Add("User-Agent", "teams-cli/1.0");
    }

    public async Task<JsonDocument> GetAsync(string pathOrUrl)
    {
        return await RetryPolicy.ExecuteAsync(async () =>
        {
            await EnsureAuthenticatedAsync();
            
            var url = pathOrUrl.StartsWith("http") ? pathOrUrl : $"{_baseUrl}/{pathOrUrl.TrimStart('/')}";
            var response = await _httpClient.GetAsync(url);
            
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                await RefreshTokenAsync();
                response = await _httpClient.GetAsync(url);
            }

            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                var retryAfter = response.Headers.RetryAfter?.Delta?.TotalSeconds ?? 60;
                throw new HttpRequestException($"429 - Rate limited. Retry after {retryAfter} seconds");
            }

            if ((int)response.StatusCode >= 500)
            {
                var content = await response.Content.ReadAsStringAsync();
                throw new HttpRequestException($"{(int)response.StatusCode} - Server error: {content}");
            }

            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            return JsonDocument.Parse(json);
        });
    }

    public async Task<HttpResponseMessage> PostJsonAsync(string path, object payload)
    {
        return await RetryPolicy.ExecuteAsync(async () =>
        {
            await EnsureAuthenticatedAsync();
            
            var url = $"{_baseUrl}/{path.TrimStart('/')}";
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync(url, content);
            
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                await RefreshTokenAsync();
                response = await _httpClient.PostAsync(url, content);
            }

            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                var retryAfter = response.Headers.RetryAfter?.Delta?.TotalSeconds ?? 60;
                throw new HttpRequestException($"429 - Rate limited. Retry after {retryAfter} seconds");
            }

            if ((int)response.StatusCode >= 500)
            {
                var responseContent = await response.Content.ReadAsStringAsync();
                throw new HttpRequestException($"{(int)response.StatusCode} - Server error: {responseContent}");
            }

            response.EnsureSuccessStatusCode();
            return response;
        });
    }

    private async Task EnsureAuthenticatedAsync()
    {
        var token = await _authService.GetAccessTokenAsync();
        _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }

    private async Task RefreshTokenAsync()
    {
        _httpClient.DefaultRequestHeaders.Authorization = null;
        await EnsureAuthenticatedAsync();
    }

    public void Dispose()
    {
        _httpClient?.Dispose();
    }
}