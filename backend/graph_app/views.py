from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Node, Edge

@csrf_exempt
@require_http_methods(["GET", "POST"])
def node_list_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if not isinstance(data.get('nodes'), list):
                return JsonResponse({'error': 'Invalid data format'}, status=400)
                
            node = Node.objects.all().delete()
            node = Node.objects.create(data=data['nodes'])

            edges = Edge.objects.all().delete()
            edges = Edge.objects.create(data=data["edges"])
            
            return JsonResponse({'id': node.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    # GET
    nodes = Node.objects.all()
    return JsonResponse([{'id': node.id, 'data': node.data} for node in nodes], safe=False)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def node_detail(request, pk):
    try:
        node = Node.objects.get(pk=pk)
    except Node.DoesNotExist:
        return JsonResponse({'error': 'Node not found'}, status=404)

    if request.method == "GET":
        return JsonResponse({'id': node.id, 'data': node.data})

    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            if not isinstance(data.get('data'), dict):
                return JsonResponse({'error': 'Invalid data format'}, status=400)
            node.data = data['data']
            node.save()
            return JsonResponse({'id': node.id, 'data': node.data})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # DELETE
    node.delete()
    return JsonResponse({'message': 'Node deleted'})
