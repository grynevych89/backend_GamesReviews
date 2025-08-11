from urllib.parse import urlparse, parse_qs
from django.shortcuts import redirect
from django.urls import reverse


def extract_site_from_referer(request, param="site"):
    referer = request.META.get("HTTP_REFERER", "")
    parsed = urlparse(referer)
    return parse_qs(parsed.query).get(param, [None])[0]

def redirect_back_to_filtered_list(request, view_name, param="site"):
    site = request.GET.get(param) or extract_site_from_referer(request, param)
    if site and str(site).isdigit():
        return redirect(f"{reverse(view_name)}?{param}={site}")
    return None
