package com.wasel.maragha;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final String DEFAULT_URL =
        "https://goal-court-birth-dana.trycloudflare.com";

    private WebView webView;
    private SharedPreferences prefs;
    private GeolocationPermissions.Callback locationCallback;
    private String locationOrigin;

    private int dp(int value) {
        return (int)(value * getResources().getDisplayMetrics().density);
    }

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);

        prefs = getSharedPreferences("wasel_settings", MODE_PRIVATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF101827);

        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(12), 0, dp(8), 0);

        TextView title = new TextView(this);
        title.setText("وصل المراغة 🛵");
        title.setTextColor(0xFFFFFFFF);
        title.setTextSize(19);
        title.setGravity(Gravity.CENTER_VERTICAL);

        Button settings = new Button(this);
        settings.setText("رابط الموقع");
        settings.setTextSize(12);

        bar.addView(title, new LinearLayout.LayoutParams(
            0, dp(54), 1
        ));
        bar.addView(settings, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, dp(48)
        ));

        webView = new WebView(this);
        webView.setBackgroundColor(0xFF101827);

        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setGeolocationEnabled(true);
        ws.setAllowFileAccess(false);
        ws.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(
                WebView view,
                android.webkit.WebResourceRequest request
            ) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();

                if ("https".equalsIgnoreCase(scheme) ||
                    "http".equalsIgnoreCase(scheme)) {
                    return false;
                }

                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this,
                        "لا يوجد تطبيق لفتح هذا الرابط",
                        Toast.LENGTH_SHORT).show();
                }
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(
                String origin,
                GeolocationPermissions.Callback callback
            ) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED ||
                    checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED) {
                    callback.invoke(origin, true, false);
                } else {
                    locationOrigin = origin;
                    locationCallback = callback;
                    requestPermissions(
                        new String[]{
                            Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION
                        }, 100
                    );
                }
            }
        });

        root.addView(bar);
        root.addView(webView, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1
        ));

        setContentView(root);

        settings.setOnClickListener(v -> showUrlDialog());

        String url = prefs.getString("url", DEFAULT_URL);
        webView.loadUrl(url);

        if (!prefs.contains("url")) {
            showUrlDialog();
        }
    }

    private void showUrlDialog() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setHint("https://your-site.trycloudflare.com");
        input.setText(prefs.getString("url", DEFAULT_URL));

        new AlertDialog.Builder(this)
            .setTitle("رابط سيرفر وصل المراغة")
            .setMessage("ضع رابط الموقع الذي يعمل حاليًا")
            .setView(input)
            .setPositiveButton("حفظ وفتح", (dialog, which) -> {
                String url = input.getText().toString().trim();

                Uri uri = Uri.parse(url);
                if (!"https".equalsIgnoreCase(uri.getScheme()) ||
                    uri.getHost() == null) {
                    Toast.makeText(this,
                        "أدخل رابط HTTPS صحيحًا",
                        Toast.LENGTH_LONG).show();
                    return;
                }

                prefs.edit().putString("url", url).apply();
                webView.loadUrl(url);
            })
            .setNegativeButton("إلغاء", null)
            .show();
    }

    @Override
    public void onRequestPermissionsResult(
        int requestCode, String[] permissions, int[] results
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, results);

        if (requestCode == 100 && locationCallback != null) {
            boolean granted = false;
            for (int result : results) {
                if (result == PackageManager.PERMISSION_GRANTED) {
                    granted = true;
                }
            }
            locationCallback.invoke(locationOrigin, granted, false);
            locationCallback = null;
            locationOrigin = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
